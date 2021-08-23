# setup (or activate) your virtual environment
if [ ! -d ./venv ]; then
 	python3 -m venv ./venv
	source ./venv/bin/activate
	python3 -m pip install -r ../requirements.txt
else
	source ./venv/bin/activate
fi

#enter private key here
export KEY_PRIVATE=""

#enter infura API key at the end of URL, or replace with a custom RPC
export RPC_ENDPOINT="https://kovan.infura.io/v3/<YOUR_INFURA_API_KEY>"

python3 single_swap.py

deactivate
