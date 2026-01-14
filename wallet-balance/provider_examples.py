from web3 import Web3

RPC_URL = "https://YOUR_NODE_ENDPOINT"  # QuickNode, Ankr, etc.
TOKEN_ADDRESS = "0xYourTokenAddress"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected()

ERC20_ABI = [
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
    }
]
contract = w3.eth.contract(
    address=Web3.to_checksum_address(TOKEN_ADDRESS),
    abi=ERC20_ABI,
)

total_supply = contract.functions.totalSupply().call()  # latest by default
print(total_supply)



# =========================== 


import requests
import json

payload = {
    "jsonrpc": "2.0",
    "method": "eth_call",
    "params": [
        {
            "to": TOKEN_ADDRESS,
            "data": "0x18160ddd"  # totalSupply()
        },
        "latest"
    ],
    "id": 1
}

response = requests.post(RPC_URL, json=payload)
result = response.json()["result"]

total_supply = int(result, 16)
print(total_supply)



# =====================

def build_eth_call_params(
    to_address: str,
    data: str,
    block: str | int = "latest"
) -> list:
    """
    Builds the params structure for eth_call.

    block:
      - "latest", "earliest", "pending"
      - or integer block number
    """
    if isinstance(block, int):
        block = hex(block)

    return [
        {
            "to": to_address,
            "data": data,
        },
        block,
    ]


def build_json_rpc_payload(
    method: str,
    params: list,
    request_id: int = 1
) -> dict:
    """
    Builds a JSON-RPC payload.
    """
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id,
    }


import requests

def execute_eth_call(
    rpc_url: str,
    to_address: str,
    data: str,
    block: str | int = "latest",
) -> int:
    """
    Executes eth_call and returns decoded integer result.
    """
    params = build_eth_call_params(
        to_address=to_address,
        data=data,
        block=block,
    )

    payload = build_json_rpc_payload(
        method="eth_call",
        params=params,
    )

    response = requests.post(rpc_url, json=payload, timeout=30)
    response.raise_for_status()

    result = response.json()

    if "error" in result:
        raise RuntimeError(result["error"])

    return int(result["result"], 16)


def get_total_supply_raw(
    rpc_url: str,
    token_address: str,
    block: str | int = "latest"
) -> int:
    """
    Returns raw totalSupply using eth_call.
    """
    TOTAL_SUPPLY_SELECTOR = "0x18160ddd"  # keccak256("totalSupply()")[:4]

    return execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=TOTAL_SUPPLY_SELECTOR,
        block=block,
    )

# Example usage - latest

RPC_URL = "https://YOUR_RPC_ENDPOINT"
TOKEN_ADDRESS = "0xYourTokenAddress"

supply = get_total_supply_raw(
    rpc_url=RPC_URL,
    token_address=TOKEN_ADDRESS,
)

print("Raw totalSupply:", supply)

# Example historical block
block_number = 19000000  # example

supply_at_block = get_total_supply_raw(
    rpc_url=RPC_URL,
    token_address=TOKEN_ADDRESS,
    block=block_number,
)

print("Raw totalSupply at block:", supply_at_block)

# -----------------------------------
# get decimal for token


def get_token_decimals_raw(
    rpc_url: str,
    token_address: str,
    block: str | int = "latest",
) -> int | None:
    DECIMALS_SELECTOR = "0x313ce567"

    value = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=DECIMALS_SELECTOR,
        block=block,
    )

    if value is None:
        return None

    return value  # already an int
