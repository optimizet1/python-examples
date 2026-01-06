import os

def get_moralis_api_key():
    return os.getenv('MORALIS_API_KEY', '')

def get_alchemy_eth_url():
    return os.getenv('ALCHEMY_ETH_URL', '')

# Provider + Wallet Config (unchanged)
PROVIDERS = {
    "eth": {
        "provider": "alchemy",
        "alchemy_url": get_alchemy_eth_url()
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
