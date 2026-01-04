import os

MORALIS_API_KEY = os.environ["MORALIS_API_KEY"]
ALCHEMY_ETH_URL = os.environ["ALCHEMY_ETH_URL"]

# Provider + Wallet Config (unchanged)
PROVIDERS = {
    "eth": {
        "provider": "alchemy",
        "alchemy_url": ALCHEMY_ETH_URL
    },
    "bsc": {
        "provider": "moralis",
        "moralis_chain": "bsc"
    }
}

CHAIN_CONFIG = {
    "eth": {
        "wallet": "0xYourEthereumWallet",
        "tokens": ["0xToken1ETH", "0xToken2ETH"]
    },
    "bsc": {
        "wallet": "0xYourBscWallet",
        "tokens": ["0xToken1BSC", "0xToken2BSC"]
    }
}
