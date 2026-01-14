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

# ERC-20 decimals() selector
DECIMALS_SELECTOR = "0x313ce567"  # keccak256("decimals()")[:4]
# ERC-20 totalSupply() selector
TOTAL_SUPPLY_SELECTOR = "0x18160ddd"  # keccak256("totalSupply()")[:4]
SYMBOL_SELECTOR   = "0x95d89b41"  # keccak256("symbol()")[:4]

DECIMALS_CACHE: dict[str, int] = {}

# DECIMALS_CACHE = {
#     "eth": {
#         "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
#             "decimals": 6,
#             "symbol": "USDC",
#         }
#     },
#     "bsc": {
#         "0x55d398326f99059ff775485246999027b3197955": {
#             "decimals": 18,
#             "symbol": "USDT",
#         }
#     }
# }



def get_token_decimals_raw(
    rpc_url: str,
    token_address: str,
    block: str | int = "latest",
) -> int | None:
    

    value = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=DECIMALS_SELECTOR,
        block=block,
    )

    if value is None:
        return None

    return value  # already an int


def get_bsc_token_decimals(
    rpc_url: str,
    token_address: str,
) -> int | None:
    """
    Returns ERC-20 decimals for a BSC token.
    Cached after first successful call.
    """

    token_address = token_address.lower()

    if token_address in DECIMALS_CACHE:
        return DECIMALS_CACHE[token_address]

    value = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=DECIMALS_SELECTOR,
        block="latest",
    )

    if value is None:
        return None

    DECIMALS_CACHE[token_address] = value
    return value


def get_bsc_tokens_decimals(
    rpc_url: str,
    chain_config: dict,
) -> dict[str, int | None]:
    """
    Returns decimals for all BSC tokens in CHAIN_CONFIG.

    Output:
    {
        "0xToken1BSC": 18,
        "0xToken2BSC": 9,
    }
    """

    results: dict[str, int | None] = {}

    tokens = chain_config.get("bsc", {}).get("tokens", [])

    for token in tokens:
        decimals = get_bsc_token_decimals(
            rpc_url=rpc_url,
            token_address=token,
        )
        results[token] = decimals

    return results

# Example usage
def example_decimal_usage():
    BSC_RPC_URL = "https://YOUR_BSC_RPC_ENDPOINT"

    bsc_decimals = get_bsc_tokens_decimals(
        rpc_url=BSC_RPC_URL,
        chain_config=CHAIN_CONFIG,
    )

    for token, decimals in bsc_decimals.items():
        print(token, "→ decimals:", decimals)



# --------------------
# total supply

def get_bsc_token_total_supply(
    rpc_url: str,
    token_address: str,
    block: str | int = "latest",
) -> int | None:
    """
    Returns raw totalSupply (uint256) for a BSC token at a given block.

    Returns:
      - int: raw on-chain totalSupply
      - None: if contract does not exist or function not callable
    """

    value = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=TOTAL_SUPPLY_SELECTOR,
        block=block,
    )

    return value  # already int or None


def get_bsc_tokens_total_supply(
    rpc_url: str,
    chain_config: dict,
    block: str | int = "latest",
) -> dict[str, int | None]:
    """
    Returns raw totalSupply for all BSC tokens in CHAIN_CONFIG.

    Output:
    {
        "0xToken1BSC": 123456789000000000000,
        "0xToken2BSC": None,
    }
    """

    results: dict[str, int | None] = {}

    tokens = chain_config.get("bsc", {}).get("tokens", [])

    for token in tokens:
        supply = get_bsc_token_total_supply(
            rpc_url=rpc_url,
            token_address=token,
            block=block,
        )
        results[token] = supply

    return results


def example_usage_bsc_total_supply():
    BSC_RPC_URL = "https://YOUR_BSC_RPC_ENDPOINT"

    supplies = get_bsc_tokens_total_supply(
        rpc_url=BSC_RPC_URL,
        chain_config=CHAIN_CONFIG,
    )

    for token, raw_supply in supplies.items():
        print(token, "→ raw totalSupply:", raw_supply)


def example_usage_bsc_total_supply_historical_block():
    BSC_RPC_URL = "https://YOUR_BSC_RPC_ENDPOINT"

    block_number = 35000000  # example BSC block

    supplies_at_block = get_bsc_tokens_total_supply(
        rpc_url=BSC_RPC_URL,
        chain_config=CHAIN_CONFIG,
        block=block_number,
    )


def get_eth_token_total_supply(
    rpc_url: str,
    token_address: str,
    block: str | int = "latest",
) -> int | None:
    """
    Returns raw totalSupply (uint256) for an ETH ERC-20 token
    at a given block.

    Returns:
      - int: raw on-chain totalSupply
      - None: if contract does not exist or function not callable
    """

    value = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=TOTAL_SUPPLY_SELECTOR,
        block=block,
    )

    return value  # already int or None

def get_eth_tokens_total_supply(
    rpc_url: str,
    chain_config: dict,
    block: str | int = "latest",
) -> dict[str, int | None]:
    """
    Returns raw totalSupply for all ETH tokens in CHAIN_CONFIG.

    Output:
    {
        "0xToken1ETH": 123456789000000000000,
        "0xToken2ETH": None,
    }
    """

    results: dict[str, int | None] = {}

    tokens = chain_config.get("eth", {}).get("tokens", [])

    for token in tokens:
        supply = get_eth_token_total_supply(
            rpc_url=rpc_url,
            token_address=token,
            block=block,
        )
        results[token] = supply

    return results

def example_usage_eth_total_supply_latest():
    ETH_RPC_URL = "https://YOUR_ETH_RPC_ENDPOINT"

    eth_supplies = get_eth_tokens_total_supply(
        rpc_url=ETH_RPC_URL,
        chain_config=CHAIN_CONFIG,
    )

    for token, raw_supply in eth_supplies.items():
        print(token, "→ raw totalSupply:", raw_supply)

def example_usage_eth_total_supply_historical():
    block_number = 19000000  # example ETH block

    eth_supplies_at_block = get_eth_tokens_total_supply(
        rpc_url=ETH_RPC_URL,
        chain_config=CHAIN_CONFIG,
        block=block_number,
    )


# - ENhanced version to get metadata and store in cache
def get_token_metadata(
    rpc_url: str,
    chain: str,
    token_address: str,
) -> dict | None:
    """
    Returns token metadata (decimals, symbol) for an ERC-20 token.
    Cached per (chain, token).

    Output:
    {
        "decimals": 18,
        "symbol": "USDT"
    }
    """

    chain = chain.lower()
    token_key = token_address.lower()

    # Ensure chain bucket exists
    DECIMALS_CACHE.setdefault(chain, {})

    # Cache hit
    if token_key in DECIMALS_CACHE[chain]:
        return DECIMALS_CACHE[chain][token_key]

    # --- decimals ---
    decimals = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=DECIMALS_SELECTOR,
        block="latest",
    )

    if decimals is None:
        return None

    # --- symbol ---
    symbol_raw = execute_eth_call(
        rpc_url=rpc_url,
        to_address=token_address,
        data=SYMBOL_SELECTOR,
        block="latest",
    )

    # symbol() may return bytes32 or string depending on token
    symbol = None
    if isinstance(symbol_raw, int):
        # bytes32 encoded as int (rare but happens)
        symbol = bytes.fromhex(hex(symbol_raw)[2:]).rstrip(b"\x00").decode("utf-8", errors="ignore")
    elif isinstance(symbol_raw, str):
        symbol = symbol_raw

    metadata = {
        "decimals": decimals,
        "symbol": symbol,
    }

    # Cache it
    DECIMALS_CACHE[chain][token_key] = metadata

    return metadata

def get_bsc_tokens_metadata(
    rpc_url: str,
    chain_config: dict,
) -> dict[str, dict | None]:
    """
    Returns decimals + symbol for all BSC tokens.
    """

    results = {}
    tokens = chain_config.get("bsc", {}).get("tokens", [])

    for token in tokens:
        results[token] = get_token_metadata(
            rpc_url=rpc_url,
            chain="bsc",
            token_address=token,
        )

    return results

def get_eth_tokens_metadata(
    rpc_url: str,
    chain_config: dict,
) -> dict[str, dict | None]:
    """
    Returns decimals + symbol for all ETH tokens.
    """

    results = {}
    tokens = chain_config.get("eth", {}).get("tokens", [])

    for token in tokens:
        results[token] = get_token_metadata(
            rpc_url=rpc_url,
            chain="eth",
            token_address=token,
        )

    return results




# -----------------------------------------------------
# Unified helpers

RPC_URLS = {
    "eth": "https://YOUR_ETH_RPC_ENDPOINT",
    "bsc": "https://YOUR_BSC_RPC_ENDPOINT",
}

TOTAL_SUPPLY_SELECTOR = "0x18160ddd"  # keccak256("totalSupply()")[:4]



def get_token_total_supply(
    chain: str,
    rpc_urls: dict,
    token_address: str,
    block: str | int = "latest",
) -> int | None:
    """
    Returns raw totalSupply (uint256) for an ERC-20 token
    on any EVM chain (ETH, BSC, etc.).

    Returns:
      - int: raw on-chain totalSupply
      - None: if contract does not exist or function not callable
    """

    chain = chain.lower()

    if chain not in rpc_urls:
        raise ValueError(f"No RPC URL configured for chain '{chain}'")

    return execute_eth_call(
        rpc_url=rpc_urls[chain],
        to_address=token_address,
        data=TOTAL_SUPPLY_SELECTOR,
        block=block,
    )

def get_chain_tokens_total_supply(
    chain: str,
    rpc_urls: dict,
    chain_config: dict,
    block: str | int = "latest",
) -> dict[str, int | None]:
    """
    Returns raw totalSupply for all tokens on a given chain.

    Output:
    {
        "0xToken1": 123456789000000000000,
        "0xToken2": None,
    }
    """

    chain = chain.lower()

    results: dict[str, int | None] = {}

    tokens = chain_config.get(chain, {}).get("tokens", [])

    for token in tokens:
        results[token] = get_token_total_supply(
            chain=chain,
            rpc_urls=rpc_urls,
            token_address=token,
            block=block,
        )

    return results

def get_all_tokens_total_supply(
    rpc_urls: dict,
    chain_config: dict,
    block: str | int = "latest",
) -> dict[str, dict[str, int | None]]:
    """
    Returns raw totalSupply for all tokens across all chains.

    Output:
    {
        "eth": {
            "0xToken1ETH": 123,
            "0xToken2ETH": None,
        },
        "bsc": {
            "0xToken1BSC": 456,
            "0xToken2BSC": 789,
        }
    }
    """

    results: dict[str, dict[str, int | None]] = {}

    for chain in chain_config.keys():
        results[chain] = get_chain_tokens_total_supply(
            chain=chain,
            rpc_urls=rpc_urls,
            chain_config=chain_config,
            block=block,
        )

    return results

def example_usage_latest_supply_for_all_chains():
    supplies = get_all_tokens_total_supply(
    rpc_urls=RPC_URLS,
    chain_config=CHAIN_CONFIG,
    )

    print(supplies)

def example_usage_historic_supply_for_all_chains():
    supplies_at_block = get_all_tokens_total_supply(
    rpc_urls=RPC_URLS,
    chain_config=CHAIN_CONFIG,
    block=19000000,  # ETH example
    )
    print(supplies_at_block)


#------------------------------
# Market Cap

def calculate_market_cap_usd(
    raw_supply: int | None,
    decimals: int | None,
    price_usd: float | None,
) -> float | None:
    """
    Market cap = (raw_supply / 10**decimals) * price_usd
    """
    if raw_supply is None or decimals is None or price_usd is None:
        return None

    human_supply = raw_supply / (10 ** decimals)
    return human_supply * price_usd


def get_token_market_cap_at_date(
    chain: str,
    rpc_urls: dict,
    token_address: str,
    date_str: str,
) -> dict:
    """
    Returns full market-cap breakdown for a single token.

    Output:
    {
        "symbol": "USDT",
        "decimals": 18,
        "raw_supply": 123456789000000000000,
        "price_usd": 0.99,
        "market_cap_usd": 1.22e11
    }
    """

    chain = chain.lower()

    # 1️⃣ total supply (raw)
    raw_supply = get_token_total_supply(
        chain=chain,
        rpc_urls=rpc_urls,
        token_address=token_address,
        block="latest",   # or date→block if you extend
    )

    # 2️⃣ metadata (cached)
    metadata = get_token_metadata(
        rpc_url=rpc_urls[chain],
        chain=chain,
        token_address=token_address,
    )

    decimals = metadata["decimals"] if metadata else None
    symbol = metadata["symbol"] if metadata else None

    # 3️⃣ price (USD)
    price_usd = get_token_price_at_date_moralis(
        chain=chain,
        token=token_address,
        date_str=date_str,
    )

    # 4️⃣ market cap
    market_cap = calculate_market_cap_usd(
        raw_supply=raw_supply,
        decimals=decimals,
        price_usd=price_usd,
    )

    return {
        "symbol": symbol,
        "decimals": decimals,
        "raw_supply": raw_supply,
        "price_usd": price_usd,
        "market_cap_usd": market_cap,
    }


def get_chain_market_caps_at_date(
    chain: str,
    rpc_urls: dict,
    chain_config: dict,
    date_str: str,
) -> dict[str, dict]:
    """
    Returns market caps for all tokens on a given chain.
    """

    chain = chain.lower()
    results: dict[str, dict] = {}

    tokens = chain_config.get(chain, {}).get("tokens", [])

    for token in tokens:
        results[token] = get_token_market_cap_at_date(
            chain=chain,
            rpc_urls=rpc_urls,
            token_address=token,
            date_str=date_str,
        )

    return results


def get_all_chains_market_caps_at_date(
    rpc_urls: dict,
    chain_config: dict,
    date_str: str,
) -> dict[str, dict[str, dict]]:
    """
    Returns market caps for all tokens across all configured chains.

    Output:
    {
        "eth": {
            "0xTokenETH": {...}
        },
        "bsc": {
            "0xTokenBSC": {...}
        }
    }
    """

    results: dict[str, dict[str, dict]] = {}

    for chain in chain_config.keys():
        results[chain] = get_chain_market_caps_at_date(
            chain=chain,
            rpc_urls=rpc_urls,
            chain_config=chain_config,
            date_str=date_str,
        )

    return results


def example_usage_market_cap():
    date = "2026-01-08"

    market_caps = get_all_chains_market_caps_at_date(
        rpc_urls=RPC_URLS,
        chain_config=CHAIN_CONFIG,
        date_str=date,
    )

    for chain, tokens in market_caps.items():
        print(chain.upper())
        for token, data in tokens.items():
            print(
                data["symbol"],
                "→ Market Cap USD:",
                data["market_cap_usd"]
            )


#-----------------
# Moralis Price Helper


def get_token_price_at_date_moralis(
    chain: str,
    token: str,
    date_str: str,
    vs_currency: str = "usd"
) -> float | None:
    """
    Returns token price (USD by default) at a given date using Moralis.

    NOTE:
    - Date-based, not block-exact
    - Uses Moralis indexed DEX pricing
    """
    chain = chain.lower()
    moralis_chain = MORALIS_CHAIN_MAP.get(chain)

    if not moralis_chain:
        raise ValueError(f"Unsupported chain for Moralis: {chain}")

    try:
        result = evm_api.token.get_token_price(
            api_key=MORALIS_API_KEY,
            params={
                "chain": moralis_chain,
                "address": token,
                "to_date": date_str,
                "exchange": "uniswapv2",  # optional but recommended
                "vs_currency": vs_currency,
            },
        )
        return float(result["usdPrice"])
    except Exception:
        return None
