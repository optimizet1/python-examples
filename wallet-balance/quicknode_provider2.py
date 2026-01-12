from web3 import Web3
from datetime import datetime, timezone
from typing import Dict, List, Optional

# ============================================================
# CONFIG (inline to keep this file self-contained)
# ============================================================

QUICKNODE_RPC = {
    "eth": "https://YOUR-ETH-ENDPOINT.quiknode.pro/YOUR_KEY/",
    "bsc": "https://YOUR-BSC-ENDPOINT.quiknode.pro/YOUR_KEY/",
}

CHAIN_CONFIG = {
    "eth": {
        "tokens": ["0xToken1ETH", "0xToken2ETH"]
    },
    "bsc": {
        "tokens": ["0xToken1BSC", "0xToken2BSC"]
    }
}

BLOCK_HISTORY = {
    "bsc": {
        "2026-01-01": 1111111,
        "2026-01-02": 1111112,
    },
    "eth": {
        "2026-01-01": 546111,
        "2026-01-02": 547111,
    }
}

# ------------------------------------------------------------
# Token contract cache (per chain)
# ------------------------------------------------------------
TOKEN_CONTRACT = {
    "eth": {
        # USDC
        "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": None,
        # DAI
        "0x6B175474E89094C44Da98b954EedeAC495271d0F": None,
    },
    "bsc": {
        # BUSD
        "0xe9e7cea3dedca5984780bafc599bd69add087d56": None,
        # USDT
        "0x55d398326f99059fF775485246999027B3197955": None,
    }
}



ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# ============================================================
# ABIs
# ============================================================

ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
]

TRANSFER_EVENT_SIG = Web3.keccak(
    text="Transfer(address,address,uint256)"
).hex()

# ============================================================
# WEB3 PROVIDER CACHE
# ============================================================

_PROVIDERS: Dict[str, Web3] = {}

def get_web3(chain: str) -> Web3:
    if chain not in _PROVIDERS:
        rpc = QUICKNODE_RPC.get(chain)
        if not rpc:
            raise ValueError(f"No RPC configured for chain {chain}")
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            raise RuntimeError(f"Failed to connect to QuickNode for {chain}")
        _PROVIDERS[chain] = w3
    return _PROVIDERS[chain]

def get_contract(chain: str, token: str):
    """
    Returns a cached ERC20 contract instance for a token.
    Creates and caches it on first use.
    """
    chain = chain.lower()
    token = Web3.to_checksum_address(token)

    # --- Return cached contract if present ---
    cached = TOKEN_CONTRACT.get(chain, {}).get(token)
    if cached:
        return cached

    # --- Create contract ---
    w3 = get_web3(chain)
    contract = w3.eth.contract(
        address=token,
        abi=ERC20_ABI,
    )

    # --- Cache and return ---
    TOKEN_CONTRACT.setdefault(chain, {})[token] = contract
    return contract


# ============================================================
# DATE → BLOCK RESOLUTION
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
    """
    Resolution order:
    1. In-memory BLOCK_HISTORY
    2. QuickNode timestamp API
    3. Binary search fallback
    """
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

    # --- fallback binary search ---
    w3 = get_web3(chain)
    low, high = 0, w3.eth.block_number

    while low <= high:
        mid = (low + high) // 2
        ts_mid = w3.eth.get_block(mid)["timestamp"]
        if ts_mid < ts:
            low = mid + 1
        elif ts_mid > ts:
            high = mid - 1
        else:
            return mid

    return high

# ============================================================
# TOTAL SUPPLY (PRIMARY + RECONSTRUCTION)
# ============================================================

def get_total_supply_at_date(
    chain: str,
    token: str,
    date_str: str
) -> int:
    block = get_block_by_date(chain, date_str)
    contract = get_contract(chain, token)

    try:
        return contract.functions.totalSupply().call(
            block_identifier=block
        )
    except Exception:
        return reconstruct_total_supply(chain, token, block)

def reconstruct_total_supply(
    chain: str,
    token: str,
    to_block: int
) -> int:
    """
    Mint/Burn reconstruction (fallback only).
    """
    w3 = get_web3(chain)

    logs = w3.eth.get_logs({
        "fromBlock": 0,
        "toBlock": to_block,
        "address": Web3.to_checksum_address(token),
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
# WALLET BALANCE AT DATE
# ============================================================

def get_wallet_token_balance_at_date(
    chain: str,
    token: str,
    wallet: str,
    date_str: str
) -> int:
    block = get_block_by_date(chain, date_str)
    contract = get_contract(chain, token)

    return contract.functions.balanceOf(
        Web3.to_checksum_address(wallet)
    ).call(block_identifier=block)

def get_wallet_total_balance_at_date(
    chain: str,
    wallet: str,
    date_str: str
) -> Dict[str, int]:
    """
    Returns raw balances per token for a wallet at a date.
    """
    balances = {}
    for token in CHAIN_CONFIG[chain]["tokens"]:
        balances[token] = get_wallet_token_balance_at_date(
            chain, token, wallet, date_str
        )
    return balances

# ============================================================
# TOKEN PRICE AT DATE (IMPORTANT NOTE BELOW)
# ============================================================

def get_token_price_at_date(
    chain: str,
    token: str,
    date_str: str
) -> Optional[float]:
    """
    ⚠️ Price is NOT on-chain state.
    QuickNode RPC cannot derive historical prices.

    This function is intentionally a pluggable hook.
    """
    # Placeholder – integrate CoinGecko / CoinMarketCap / internal pricing DB
    return None
