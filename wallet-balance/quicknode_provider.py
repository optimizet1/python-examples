from web3 import Web3
import requests
from datetime import datetime
from typing import Optional, List, Dict

from settings import CHAIN_CONFIG, QUICKNODE_PROVIDER


QN_ERC20_ABI = [
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


def qn_get_block_by_timestamp(chain: str, timestamp: int) -> Optional[int]:
    provider = QUICKNODE_PROVIDER[chain]
    explorer = provider["explorer"]

    if explorer["name"] == "etherscan":
        url = "https://api.etherscan.io/api"
    elif explorer["name"] == "bscscan":
        url = "https://api.bscscan.com/api"
    else:
        raise ValueError("Unsupported explorer")

    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "before",
        "apikey": explorer["api_key"]
    }

    resp = requests.get(url, params=params).json()
    if resp.get("status") == "1":
        return int(resp["result"])
    return None


def qn_get_token_balance(w3: Web3, token: str, wallet: str, block: int) -> Optional[Dict]:
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=QN_ERC20_ABI)
        balance = contract.functions.balanceOf(wallet).call(block_identifier=block)
        decimals = contract.functions.decimals().call()
        symbol = contract.functions.symbol().call()
        return {
            "token_address": token,
            "symbol": symbol,
            "balance": balance / (10 ** decimals),
            "raw_balance": balance,
            "decimals": decimals
        }
    except Exception as e:
        print(f"❌ Error fetching {token} for {wallet}: {e}")
        return None


def qn_get_all_balances_by_date(date_str: str) -> Dict[str, List[Dict]]:
    results = {}
    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

    for chain in CHAIN_CONFIG:
        print(f"\n🔍 Checking {chain.upper()}...")

        rpc_url = QUICKNODE_PROVIDER[chain]["rpc_url"]
        wallet = Web3.to_checksum_address(CHAIN_CONFIG[chain]["wallet"])
        tokens = CHAIN_CONFIG[chain]["tokens"]

        block = qn_get_block_by_timestamp(chain, target_ts)
        if block is None:
            print(f"❌ Could not resolve block for {date_str} on {chain}")
            results[chain] = []
            continue

        print(f"📦 Block: {block}")
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        balances = []
        for token in tokens:
            result = qn_get_token_balance(w3, token, wallet, block)
            if result:
                balances.append(result)

        results[chain] = balances

    return results
