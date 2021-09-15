# setup (or activate) your virtual environment
if [ ! -d ./node_modules ]; then
 	npm install
fi

#enter private key here
export KEY_PRIVATE=""

#enter infura API key at the end of URL, or replace with a custom RPC
export RPC_ENDPOINT="https://kovan.infura.io/v3/<YOUR_INFURA_API_KEY>"

node single_swap.js
