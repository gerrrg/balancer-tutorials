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
block_explorer_url = "https://kovan.etherscan.io/"
chain_id = 42
gas_price = 2

# Load contract for Balancer Vault
address_vault = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
path_abi_vault = '../../abis/Vault.json'
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
pool_WETH_USDC = 	"0x3a19030ed746bd1c3f2b0f996ff9479af04c5f0a000200000000000000000004"
pool_BAL_WETH = 	"0x61d5dc44849c9c87b0856a2a311536205c96c7fd000200000000000000000000"

# Token addresses
token_BAL 	= "0x41286Bb1D3E870f3F750eB7E1C25d7E48c8A1Ac7".lower()
token_USDC 	= "0xc2569dd7d0fd715B054fBf16E75B001E5c0C1115".lower()
token_WETH 	= "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1".lower()

# Token data
token_data = {
	token_BAL:{
		"symbol":"BAL",
		"decimals":"18",
		"limit":"0"
	},
	token_USDC:{
		"symbol":"USDC",
		"decimals":"6",
		"limit":"100"
	},
	token_WETH:{
		"symbol":"WETH",
		"decimals":"18",
		"limit":"0"
	}
}

swap_steps = [
	{
		"poolId":pool_WETH_USDC,
		"assetIn":token_USDC,
		"assetOut":token_WETH,
		"amount": "100"
	},
	{
		"poolId":pool_BAL_WETH,
		"assetIn":token_WETH,
		"assetOut":token_BAL,
		"amount":"0"
	}
]

# SwapKind is an Enum. This example handles a GIVEN_IN swap.
# https://github.com/balancer-labs/balancer-v2-monorepo/blob/0328ed575c1b36fb0ad61ab8ce848083543070b9/pkg/vault/contracts/interfaces/IVault.sol#L497
swap_kind = 0 #0 = GIVEN_IN, 1 = GIVEN_OUT

token_addresses = list(token_data.keys())
token_addresses.sort()
token_indices = {token_addresses[idx]:idx for idx in range(len(token_addresses))}

user_data_encoded = eth_abi.encode_abi(['uint256'], [0])
swaps_step_structs = []
for step in swap_steps:
	swaps_step_struct = (
		step["poolId"],
		token_indices[step["assetIn"]],
		token_indices[step["assetOut"]],
		int(Decimal(step["amount"]) * 10 ** Decimal((token_data[step["assetIn"]]["decimals"]))),
		user_data_encoded
	)
	swaps_step_structs.append(swaps_step_struct)

fund_struct = (
	web3.toChecksumAddress(fund_settings["sender"]),
	fund_settings["fromInternalBalance"],
	web3.toChecksumAddress(fund_settings["recipient"]),
	fund_settings["toInternalBalance"]
)

token_limits = [int(Decimal(token_data[token]["limit"]) * 10 ** Decimal(token_data[token]["decimals"])) for token in token_addresses]
checksum_tokens = [web3.toChecksumAddress(token) for token in token_addresses]

batch_swap_function = contract_vault.functions.batchSwap(	
	swap_kind,
	swaps_step_structs,
	checksum_tokens,
	fund_struct,
	token_limits,
	deadline
)

try:
	gas_estimate = batch_swap_function.estimateGas()
except:
	gas_estimate = 200000
	print("Failed to estimate gas, attempting to send with", gas_estimate, "gas limit...")

data = batch_swap_function.buildTransaction(
	{
		'chainId': chain_id,
	    'gas': gas_estimate,
	    'gasPrice': web3.toWei(gas_price, 'gwei'),
	    'nonce': web3.eth.get_transaction_count(address),
	}
)

signed_tx = web3.eth.account.sign_transaction(data, private_key)
tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
print("Sending transaction...")
url = block_explorer_url + "tx/" + tx_hash
webbrowser.open_new_tab(url)
