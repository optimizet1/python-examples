from web3 import Web3
from datetime import datetime, timezone
from typing import Dict, Optional

# ============================================================
# CONFIG
# ============================================================

QUICKNODE_RPC = {
    "eth": "https://YOUR-ETH-ENDPOINT.quiknode.pro/YOUR_KEY/",
    "bsc": "https://YOUR-BSC-ENDPOINT.quiknode.pro/YOUR_KEY/",
}

BLOCK_HISTORY = {
    "eth": {},
    "bsc": {},
}

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# ============================================================
# CACHES
# ============================================================

# Contract interface cache
TOKEN_CONTRACT: Dict[str, Dict[str, object]] = {
    "eth": {},
    "bsc": {},
}

# Immutable metadata cache (once per token)
TOKEN_IMMUTABLE_CACHE: Dict[str, Dict[str, Dict]] = {
    "eth": {},
    "bsc": {},
}

# Mutable snapshot cache (block-aware)
# (chain, token, block) -> snapshot
TOKEN_SNAPSHOT_CACHE: Dict[tuple, Dict] = {}

# Web3 provider cache
_PROVIDERS: Dict[str, Web3] = {}

# ============================================================
# ABIs
# ============================================================

ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}],
    },
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
]

ERC20_IMMUTABLE_ABI = [
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint8"}],
    },
    {
        "name": "symbol",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "string"}],
    },
    {
        "name": "name",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "string"}],
    },
]

TRANSFER_EVENT_SIG = Web3.keccak(
    text="Transfer(address,address,uint256)"
).hex()

# EIP-1967 implementation slot
EIP1967_IMPL_SLOT = Web3.to_hex(
    int(Web3.keccak(text="eip1967.proxy.implementation").hex(), 16) - 1
)

# ============================================================
# WEB3 / CONTRACT HELPERS
# ============================================================

def get_web3(chain: str) -> Web3:
    chain = chain.lower()
    if chain not in _PROVIDERS:
        rpc = QUICKNODE_RPC.get(chain)
        if not rpc:
            raise ValueError(f"No RPC configured for {chain}")
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            raise RuntimeError(f"Failed to connect to QuickNode ({chain})")
        _PROVIDERS[chain] = w3
    return _PROVIDERS[chain]


def get_contract(chain: str, token: str):
    """
    Cached ERC20 contract interface (ABI + address only)
    """
    chain = chain.lower()
    token = Web3.to_checksum_address(token)

    cached = TOKEN_CONTRACT.get(chain, {}).get(token)
    if cached:
        return cached

    contract = get_web3(chain).eth.contract(
        address=token,
        abi=ERC20_ABI,
    )

    TOKEN_CONTRACT.setdefault(chain, {})[token] = contract
    return contract

# ============================================================
# DATE / BLOCK RESOLUTION
# ============================================================

def normalize_date(date_str: str) -> str:
    return (
        date_str if "-" in date_str
        else datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    )


def get_block_by_timestamp_quicknode(
    chain: str,
    timestamp: int,
    after: bool = True
) -> int:
    w3 = get_web3(chain)
    direction = "after" if after else "before"

    resp = w3.provider.make_request(
        "qn_getBlockByTimestamp",
        [timestamp, direction],
    )

    if "error" in resp:
        raise RuntimeError(resp["error"])

    return int(resp["result"]["blockNumber"], 16)


def get_block_by_date(chain: str, date_str: str) -> int:
    chain = chain.lower()
    date_key = normalize_date(date_str)

    cached = BLOCK_HISTORY.get(chain, {}).get(date_key)
    if cached:
        return cached

    ts = int(
        datetime.strptime(date_key, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )

    try:
        block = get_block_by_timestamp_quicknode(chain, ts, after=True)
        BLOCK_HISTORY.setdefault(chain, {})[date_key] = block
        return block
    except Exception:
        pass

    # Binary search fallback (last resort)
    w3 = get_web3(chain)
    low, high = 0, w3.eth.block_number

    while low <= high:
        mid = (low + high) // 2
        mid_ts = w3.eth.get_block(mid)["timestamp"]
        if mid_ts < ts:
            low = mid + 1
        elif mid_ts > ts:
            high = mid - 1
        else:
            return mid

    return high

# ============================================================
# IMMUTABLE METADATA (CACHE ONCE)
# ============================================================

def get_immutable_token_metadata(chain: str, token: str) -> Dict:
    chain = chain.lower()
    token = Web3.to_checksum_address(token)

    cached = TOKEN_IMMUTABLE_CACHE.get(chain, {}).get(token)
    if cached:
        return cached

    w3 = get_web3(chain)
    contract = w3.eth.contract(
        address=token,
        abi=ERC20_IMMUTABLE_ABI,
    )

    def safe_call(fn):
        try:
            return fn()
        except Exception:
            return None

    meta = {
        "chain": chain,
        "token": token,
        "decimals": safe_call(contract.functions.decimals().call),
        "symbol": safe_call(contract.functions.symbol().call),
        "name": safe_call(contract.functions.name().call),
    }

    TOKEN_IMMUTABLE_CACHE.setdefault(chain, {})[token] = meta
    return meta

# ============================================================
# PROXY DETECTION
# ============================================================

def detect_proxy(chain: str, token: str) -> Dict:
    w3 = get_web3(chain)
    token = Web3.to_checksum_address(token)

    try:
        raw = w3.eth.get_storage_at(token, EIP1967_IMPL_SLOT)
        impl = Web3.to_checksum_address(raw[-20:].hex())
        if int(impl, 16) != 0:
            return {
                "is_proxy": True,
                "implementation": impl,
            }
    except Exception:
        pass

    return {
        "is_proxy": False,
        "implementation": None,
    }

# ============================================================
# TOTAL SUPPLY (ARCHIVE + RECONSTRUCTION)
# ============================================================

def reconstruct_total_supply(chain: str, token: str, to_block: int) -> int:
    w3 = get_web3(chain)
    token = Web3.to_checksum_address(token)

    logs = w3.eth.get_logs({
        "fromBlock": 0,
        "toBlock": to_block,
        "address": token,
        "topics": [TRANSFER_EVENT_SIG],
    })

    supply = 0
    for log in logs:
        from_addr = "0x" + log["topics"][1].hex()[-40:]
        to_addr = "0x" + log["topics"][2].hex()[-40:]
        value = int(log["data"], 16)

        if from_addr.lower() == ZERO_ADDRESS:
            supply += value
        elif to_addr.lower() == ZERO_ADDRESS:
            supply -= value

    return supply

# ============================================================
# MUTABLE SNAPSHOT METADATA (BLOCK-AWARE)
# ============================================================

def snapshot_token_mutable_metadata(
    chain: str,
    token: str,
    date_str: str
) -> Dict:
    chain = chain.lower()
    token = Web3.to_checksum_address(token)

    block = get_block_by_date(chain, date_str)
    cache_key = (chain, token, block)

    if cache_key in TOKEN_SNAPSHOT_CACHE:
        return TOKEN_SNAPSHOT_CACHE[cache_key]

    w3 = get_web3(chain)
    contract = get_contract(chain, token)

    try:
        total_supply = contract.functions.totalSupply().call(
            block_identifier=block
        )
    except Exception:
        total_supply = reconstruct_total_supply(chain, token, block)

    proxy_info = detect_proxy(chain, token)

    snapshot = {
        "chain": chain,
        "token": token,
        "date": normalize_date(date_str),
        "block": block,
        "timestamp": w3.eth.get_block(block)["timestamp"],
        "total_supply": total_supply,
        "is_proxy": proxy_info["is_proxy"],
        "implementation": proxy_info["implementation"],
    }

    TOKEN_SNAPSHOT_CACHE[cache_key] = snapshot
    return snapshot

# ============================================================
# UNIFIED METADATA SNAPSHOT
# ============================================================

def get_token_metadata_snapshot(
    chain: str,
    token: str,
    date_str: str
) -> Dict:
    return {
        "immutable": get_immutable_token_metadata(chain, token),
        "snapshot": snapshot_token_mutable_metadata(chain, token, date_str),
    }


# ================

def get_token_decimals(chain: str, token: str) -> Optional[int]:
    """
    Immutable ERC20 metadata. Cached once per token.
    """
    meta = get_immutable_token_metadata(chain, token)
    return meta.get("decimals")


def get_token_total_supply_at_date(
    chain: str,
    token: str,
    date_str: str
) -> int:
    """
    Returns totalSupply at a given date.
    Uses archive call first, mint/burn reconstruction as fallback.
    """
    block = get_block_by_date(chain, date_str)
    contract = get_contract(chain, token)

    try:
        return contract.functions.totalSupply().call(
            block_identifier=block
        )
    except Exception:
        return reconstruct_total_supply(chain, token, block)


def get_token_balance_at_date(
    chain: str,
    token: str,
    wallet: str,
    date_str: str
) -> int:
    """
    Returns balanceOf(wallet) at a given date.
    Requires historical RPC support (QuickNode OK).
    """
    block = get_block_by_date(chain, date_str)
    contract = get_contract(chain, token)

    return contract.functions.balanceOf(
        Web3.to_checksum_address(wallet)
    ).call(block_identifier=block)

def get_token_balance_human_at_date(
    chain: str,
    token: str,
    wallet: str,
    date_str: str
) -> float:
    raw = get_token_balance_at_date(chain, token, wallet, date_str)
    decimals = get_token_decimals(chain, token) or 0
    return raw / (10 ** decimals)


def get_token_total_supply_human_at_date(
    chain: str,
    token: str,
    date_str: str
) -> float:
    raw = get_token_total_supply_at_date(chain, token, date_str)
    decimals = get_token_decimals(chain, token) or 0
    return raw / (10 ** decimals)

