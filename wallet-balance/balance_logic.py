import datetime
from web3 import Web3
from moralis import evm_api
from settings import MORALIS_API_KEY, PROVIDERS, CHAIN_CONFIG
import re
import os
from common import get_boolean_from_value, is_date_older_than_cutoff

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def get_block_by_date(date_str: str, chain: str) -> int:
    iso_timestamp = f"{date_str}T00:00:00Z"
    provider = PROVIDERS[chain]["provider"]

    if provider == "moralis":

        use_block_env_var = get_boolean_from_value(os.environ.get('USE_BLOCK_FROM_ENV', 'false'))

        if use_block_env_var:
            block_num = int(os.environ.get('MORALIS_BLOCK_NUMBER', 0))

            if block_num > 71000000:
                return block_num


        result = evm_api.block.get_date_to_block(
            api_key=MORALIS_API_KEY,
            params={
                "chain": PROVIDERS[chain]["moralis_chain"],
                "date": iso_timestamp
            }
        )
        return int(result["block"])

    elif provider == "alchemy":
        import requests
        ts = int(datetime.datetime.fromisoformat(date_str).timestamp())
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getBlockByTimestamp",
            "params": [hex(ts), "latest"]
        }
        response = requests.post(PROVIDERS[chain]["alchemy_url"], json=payload)
        response.raise_for_status()
        return int(response.json()["result"]["number"], 16)

    raise ValueError("Unsupported provider")


def get_moralis_token_balances(wallet: str, tokens: list[str], chain: str, block_number: int):
    result = evm_api.token.get_wallet_token_balances(
        api_key=MORALIS_API_KEY,
        params={
            "chain": PROVIDERS[chain]["moralis_chain"],
            "address": wallet,
            "to_block": block_number,
            "token_addresses": tokens
        }
    )
    return [
        {
            "token_address": x["token_address"],
            "symbol": x["symbol"],
            "balance": int(x["balance"]) / (10 ** int(x["decimals"])),
            "raw_balance": x["balance"],
            "decimals": x["decimals"]
        }
        for x in result
    ]


def get_alchemy_token_balance(w3: Web3, token_address: str, wallet: str, block_number: int):
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    balance = contract.functions.balanceOf(wallet).call(block_identifier=block_number)
    decimals = contract.functions.decimals().call()
    symbol = contract.functions.symbol().call()
    return {
        "token_address": token_address,
        "symbol": symbol,
        "balance": balance / (10 ** decimals),
        "raw_balance": balance,
        "decimals": decimals
    }


def get_all_balances_by_date(date: str):
    results = {}

    for chain, config in CHAIN_CONFIG.items():
        wallet = config["wallet"]
        tokens = config["tokens"]
        provider = PROVIDERS[chain]["provider"]

        wallet = validate_eth_address(wallet)
        if wallet:

            try:
                block = get_block_by_date(date, chain)

                if provider == "moralis":
                    balances = get_moralis_token_balances(wallet, tokens, chain, block)
                elif provider == "alchemy":
                    w3 = Web3(Web3.HTTPProvider(PROVIDERS[chain]["alchemy_url"]))
                    balances = [
                        get_alchemy_token_balance(w3, token, wallet, block)
                        for token in tokens
                    ]
                else:
                    balances = []

            except Exception as e:
                balances = [{"error": str(e)}]

            results[chain] = balances

    return results



def validate_eth_address(address: str) -> str | None:
    """
    Validates an Ethereum (or EVM) address.
    - Returns the checksummed address if valid
    - Returns None if invalid
    """
    if not isinstance(address, str):
        return None

    if not address.startswith("0x") and not address.startswith("0X"):
        address = "0x" + address

    if not re.fullmatch(r"0x[a-fA-F0-9]{40}", address):
        return None

    if not Web3.is_address(address):
        return None

    return Web3.to_checksum_address(address)
