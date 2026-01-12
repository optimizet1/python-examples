from web3 import Web3
import requests
from datetime import datetime
from typing import Optional, List, Dict

from settings import CHAIN_CONFIG, QUICKNODE_PROVIDER, BLOCK_HISTORY


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


def qn_get_block_by_timestamp2(chain: str, timestamp: int) -> Optional[int]:
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


def get_block_by_date(chain: str, date_str: str) -> int:
    """
    Resolve block for a given chain + date.

    Resolution order:
    1. In-memory BLOCK_HISTORY
    2. QuickNode timestamp API
    3. Binary search fallback
    """
    # --- 1️⃣ In-memory lookup ---
    date_key = normalize_date(date_str)
    cached = BLOCK_HISTORY.get(chain, {}).get(date_key)
    if cached and cached > 0:
        return cached

    # --- 2️⃣ QuickNode timestamp API ---
    dt = datetime.strptime(date_key, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )
    target_ts = int(dt.timestamp())

    try:
        block = get_block_by_timestamp_quicknode(
            chain=chain,
            timestamp=target_ts,
            after=True,
        )
        return block
    except Exception:
        pass  # fallback

    # --- 3️⃣ Binary search fallback ---
    w3 = get_web3(chain)

    latest = w3.eth.block_number
    low, high = 0, latest

    while low <= high:
        mid = (low + high) // 2
        block = w3.eth.get_block(mid)
        ts = block["timestamp"]

        if ts < target_ts:
            low = mid + 1
        elif ts > target_ts:
            high = mid - 1
        else:
            return mid

    return high


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

# -------------------------------
# Provider cache
# -------------------------------
_PROVIDERS = {}
# -------------------------------
# Token helpers
# -------------------------------
def get_contract(chain: str, token_address: str):
    w3 = get_web3(chain)
    return w3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=QN_ERC20_ABI,
    )

def get_total_supply_at_block(
    chain: str,
    token_address: str,
    block: int
) -> int:
    contract = get_contract(chain, token_address)
    return contract.functions.totalSupply().call(
        block_identifier=block
    )

def get_balance_at_block(
    chain: str,
    token_address: str,
    wallet: str,
    block: int
) -> int:
    contract = get_contract(chain, token_address)
    return contract.functions.balanceOf(
        Web3.to_checksum_address(wallet)
    ).call(block_identifier=block)


def get_web3(chain: str) -> Web3:
    if chain not in _PROVIDERS :
        rpc = QUICKNODE_PROVIDER.get(chain)
        if not rpc:
            raise ValueError(f"No RPC configured for chain: {chain}")
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            raise RuntimeError(f"Failed to connect to QuickNode for {chain}")
        _PROVIDERS[chain] = w3
    return _PROVIDERS[chain]

# -------------------------------
# Date helpers
# -------------------------------
def normalize_date(date_str: str) -> str:
    """
    Accepts YYYYMMDD or YYYY-MM-DD → YYYY-MM-DD
    """
    if "-" in date_str:
        return date_str
    return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")

def get_block_from_history(chain: str, date_str: str) -> int:
    """
    Returns block from BLOCK_HISTORY or 0 if missing
    """
    date_key = normalize_date(date_str)
    return BLOCK_HISTORY.get(chain, {}).get(date_key, 0)


# -------------------------------
# Unified block resolver
# -------------------------------
def resolve_block(chain: str, date_str: str) -> int:
    block = get_block_from_history(chain, date_str)
    if block > 0:
        return block
    return get_block_by_date(chain, date_str)



def get_block_by_timestamp_quicknode(
    chain: str,
    timestamp: int,
    after: bool = True
) -> int:
    """
    Uses QuickNode native API to resolve block by timestamp
    """
    w3 = get_web3(chain)

    direction = "after" if after else "before"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "qn_getBlockByTimestamp",
        "params": [timestamp, direction],
    }

    response = w3.provider.make_request(
        method=payload["method"],
        params=payload["params"],
    )

    if "error" in response:
        raise RuntimeError(f"QuickNode error: {response['error']}")

    return int(response["result"]["blockNumber"], 16)
