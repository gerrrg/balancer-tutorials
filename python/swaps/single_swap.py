from web3 import Web3
import eth_abi

import os
import json
from decimal import *
import webbrowser

# Load private key and connect to RPC endpoint
rpc_endpoint = 	os.environ.get("RPC_ENDPOINT")
private_key =  	os.environ.get("KEY_PRIVATE")
if rpc_endpoint is None or private_key is None or private_key == "":
	print("\n[ERROR] You must set environment variables for RPC_ENDPOINT and KEY_PRIVATE\n")
	quit()
web3 = Web3(Web3.HTTPProvider(rpc_endpoint))
account = web3.eth.account.privateKeyToAccount(private_key)
address = account.address

# Define network settings
network = "kovan"
blockExplorerUrl = "https://kovan.etherscan.io/"
chain_id = 42
gas_price = 2

# Load contract for Balancer Vault
address_vault = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
path_abi_vault = '../abis/Vault.json'
with open(path_abi_vault) as f:
  abi_vault = json.load(f)
contract_vault = web3.eth.contract(
	address=web3.toChecksumAddress(address_vault), 
	abi=abi_vault
)

# Where are the tokens coming from/going to?
fund_settings = {
	"sender":				address,
	"recipient":			address,
	"fromInternalBalance": 	False,
	"toInternalBalance": 	False
}

# When should the transaction timeout?
deadline = 999999999999999999

# Pool IDs
pool_BAL_WETH = "0x61d5dc44849c9c87b0856a2a311536205c96c7fd000200000000000000000000"

# Token addresses
token_BAL 	= "0x41286Bb1D3E870f3F750eB7E1C25d7E48c8A1Ac7"
token_WETH 	= "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1"

# Token data
token_data = {
	token_BAL:{
		"symbol":"BAL",
		"decimals":"18",
		"limit":"0"
	},
	token_WETH:{
		"symbol":"WETH",
		"decimals":"18",
		"limit":"1"
	}
}

swap = {
		"poolId":pool_BAL_WETH,
		"assetIn":token_WETH,
		"assetOut":token_BAL,
		"amount":"1"
	}

# SwapKind is an Enum. This example handles a GIVEN_IN swap.
# https://github.com/balancer-labs/balancer-v2-monorepo/blob/0328ed575c1b36fb0ad61ab8ce848083543070b9/pkg/vault/contracts/interfaces/IVault.sol#L497
swap_kind = 0 #0 = GIVEN_IN, 1 = GIVEN_OUT

user_data_encoded = eth_abi.encode_abi(['uint256'], [0])

swap_struct = (
	swap["poolId"],
	swap_kind,
	web3.toChecksumAddress(swap["assetIn"]),
	web3.toChecksumAddress(swap["assetOut"]),
	int(Decimal(swap["amount"]) * 10 ** Decimal((token_data[swap["assetIn"]]["decimals"]))),
	user_data_encoded
)

fund_struct = (
	web3.toChecksumAddress(fund_settings["sender"]),
	fund_settings["fromInternalBalance"],
	web3.toChecksumAddress(fund_settings["recipient"]),
	fund_settings["toInternalBalance"]
)

token_limit = int(Decimal(token_data[swap["assetIn"]]["limit"]) * 10 ** Decimal(token_data[swap["assetIn"]]["decimals"]))

single_swap_function = contract_vault.functions.swap(	
	swap_struct,
	fund_struct,
	token_limit,
	deadline
)

try:
	gasEstimate = single_swap_function.estimateGas()
except:
	gasEstimate = 100000
	print("Failed to estimate gas, attempting to send with", gasEstimate, "gas limit...")

data = single_swap_function.buildTransaction(
	{
		'chainId': chain_id,
	    'gas': gasEstimate,
	    'gasPrice': web3.toWei(gas_price, 'gwei'),
	    'nonce': web3.eth.get_transaction_count(address),
	}
)

signed_tx = web3.eth.account.sign_transaction(data, private_key)
tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
print("Sending transaction...")
url = blockExplorerUrl + "tx/" + tx_hash
webbrowser.open_new_tab(url)
