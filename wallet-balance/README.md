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

