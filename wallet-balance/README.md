# Token Wallet Balance
Get token balances on ETH and BSC chains. 

Update settings.py to add your contracts
Update Environment variables (when running locally update local.settings.json)

# Initialize virtual environment and install dependencies

## 1. Initialize venv
python -m venv .venv

## 2. Activate venv
On Windows CMD:
.venv\Scripts\activate

On Mac/Linux
source .venv/bin/activate

## 3. Install Dependencies

Upgrade pip version
python.exe -m pip install --upgrade pip

pip install -r requirements.txt

## 4. Install REST Client Extension in Visual Studio Code 
This is used to run/execute requests in test.http

In VS Code, go to Extensions, search for: humao.rest-client



# Start / Debug


func start


# Other

This doesn't use Blob storage. If you need it and run locally install Azurite

npm install -g azurite
azurite

# in requirements.txt
Optinally to get latest Moralis SDK
moralis @ git+https://github.com/MoralisWeb3/Moralis-Python-SDK.git



# Pricing

First: the hard truth (important)

There is no such thing as a truly block-exact price unless you:

index DEX swaps yourself

replay trades up to that exact block

compute VWAP/last price manually

Moralis (and CoinGecko, etc.) do not do this.

What is possible — and industry-standard — is:

Normalize price to the block’s timestamp
by querying the price at that timestamp’s calendar date (or nearest time bucket)

That’s what we’ll implement.

Normalization strategy (best practice)
Given:

block_number

chain

token

Steps:

Get block timestamp from QuickNode

Convert timestamp → UTC date

Ask Moralis for price at that date

Store:

block

timestamp

date

price

normalization method

This is what professional analytics pipelines do.


# Keccak256

| Function             | Signature              | Selector     |
| -------------------- | ---------------------- | ------------ |
| `totalSupply()`      | `"totalSupply()"`      | `0x18160ddd` |
| `balanceOf(address)` | `"balanceOf(address)"` | `0x70a08231` |
| `decimals()`         | `"decimals()"`         | `0x313ce567` |
| `symbol()`           | `"symbol()"`           | `0x95d89b41` |


