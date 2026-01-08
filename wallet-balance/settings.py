import os

def get_moralis_api_key():
    return os.getenv('MORALIS_API_KEY', '')

def get_alchemy_eth_url():
    return os.getenv('ALCHEMY_ETH_URL', '')

# Provider + Wallet Config (unchanged)
# PROVIDERS = {
#     "eth": {
#         "provider": "alchemy",
#         "alchemy_url": ALCHEMY_ETH_URL
#     },
#     "bsc": {
#         "provider": "moralis",
#         "moralis_chain": "bsc"
#     }
# }

# CHAIN_CONFIG = {
#     "eth": {
#         "wallet": "0xYourEthereumWallet",
#         "tokens": ["0xToken1ETH", "0xToken2ETH"]
#     },
#     "bsc": {
#         "wallet": "0xYourBscWallet",
#         "tokens": ["0xToken1BSC", "0xToken2BSC"]
#     }
# }


PROVIDERS = {
    "bsc": {
        "provider": "moralis",
        "moralis_chain": "bsc"
    }
}

# CHAIN_CONFIG = {
#     "bsc": {
#         "wallet": "0xYourBscWallet",
#         "tokens": ["0xToken1BSC", "0xToken2BSC"]
#     }
# }

CHAIN_CONFIG = {

 "bsc": {
 "wallet": "0xb33A6BDF4192Ebd826ee14967C48F08D3B889fAd",
 "tokens": ["0x7048f5227b032326cc8dbc53cf3fddd947a2c757",
 "0x091fc7778e6932d4009b087b191d1ee3bac5729a",
"0x2494b603319d4d9f9715c9f4496d9e0364b59d93"]
 }
}

# CONFIG = {
# "e": {
# "w": "0x3312cc371Fe0Dd5171878630A1E5cf69778E8fa5",
# "t": ["0x032dec3372f25c41ea8054b4987a7c4832cdb338",
# "0xba47214edd2bb43099611b208f75e4b42fdcfedc",
# "0xf6b1117ec07684d3958cad8beb1b302bfd21103f"]
#  },
#  "b": {
#  "w": "0xb33A6BDF4192Ebd826ee14967C48F08D3B889fAd",
#  "t": ["0x7048f5227b032326cc8dbc53cf3fddd947a2c757",
#  "0x091fc7778e6932d4009b087b191d1ee3bac5729a",
# "0x2494b603319d4d9f9715c9f4496d9e0364b59d93"]
#  }
# }


QUICKNODE_PROVIDER = {
    "eth": {
        "rpc_url": "https://eth-mainnet.quiknode.pro/<your-eth-id>/",
        "explorer": {
            "name": "etherscan",
            "api_key": "YOUR_ETHERSCAN_API_KEY"
        }
    },
    "bsc": {
        "rpc_url": "https://bsc-mainnet.quiknode.pro/<your-bsc-id>/",
        "explorer": {
            "name": "bscscan",
            "api_key": "YOUR_BSCSCAN_API_KEY"
        }
    }
}


# ERC20_ABI = [
#     {
#         "constant": True,
#         "inputs": [{"name": "_owner", "type": "address"}],
#         "name": "balanceOf",
#         "outputs": [{"name": "balance", "type": "uint256"}],
#         "type": "function"
#     },
#     {
#         "constant": True,
#         "inputs": [],
#         "name": "decimals",
#         "outputs": [{"name": "", "type": "uint8"}],
#         "type": "function"
#     },
#     {
#         "constant": True,
#         "inputs": [],
#         "name": "symbol",
#         "outputs": [{"name": "", "type": "string"}],
#         "type": "function"
#     }
# ]
