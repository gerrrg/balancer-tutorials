const Web3 = require("web3");
const fs = require("fs");
const BigNumber = require("bignumber.js");
const Tx = require('ethereumjs-tx').Transaction;
const open = require('open');

// Load private key and connect to RPC endpoint
const rpc_endpoint = process.env.RPC_ENDPOINT;
const private_key = process.env.KEY_PRIVATE;
if (rpc_endpoint == undefined || private_key == undefined || private_key == "") {
    throw new Error("You must set environment variables for RPC_ENDPOINT and KEY_PRIVATE");
}
const web3 = new Web3(new Web3.providers.HttpProvider(rpc_endpoint));
const account = web3.eth.accounts.privateKeyToAccount(private_key);
const address = account.address;

// Define network settings
const network = "kovan";
const block_explorer_url = "https://kovan.etherscan.io/";
const chain_id = "42";
const gas_price = "2";

// Load contract for Balancer Vault
const address_vault = "0xBA12222222228d8Ba445958a75a0704d566BF2C8";
const path_abi_vault = "../../abis/Vault.json";
let abi_vault = JSON.parse(fs.readFileSync(path_abi_vault));
const contract_vault = new web3.eth.Contract(abi_vault, address_vault);

// Where are the tokens coming from/going to?
const fund_settings = {
    "sender":               address,
    "recipient":            address,
    "fromInternalBalance":  false,
    "toInternalBalance":    false
};

// When should the transaction timeout?
const deadline = BigNumber(999999999999999999);

// Pool IDs
const pool_BAL_WETH = "0x61d5dc44849c9c87b0856a2a311536205c96c7fd000200000000000000000000";

// Token addresses (checksum format)
const token_BAL = "0x41286Bb1D3E870f3F750eB7E1C25d7E48c8A1Ac7".toLowerCase();
const token_WETH = "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1".toLowerCase();

// Token data
const token_data = {};
token_data[token_BAL] = 
    {
        "symbol": "BAL",
        "decimals": "18",
        "limit": "0"
    };
token_data[token_WETH] = 
    {
        "symbol": "WETH",
        "decimals": "18",
        "limit": "1"
    };

const swap = {
    "poolId": pool_BAL_WETH,
    "assetIn": token_WETH,
    "assetOut": token_BAL,
    "amount": 1
};

// SwapKind is an Enum. This example handles a GIVEN_IN swap.
// https://github.com/balancer-labs/balancer-v2-monorepo/blob/0328ed575c1b36fb0ad61ab8ce848083543070b9/pkg/vault/contracts/interfaces/IVault.sol#L497
// 0 = GIVEN_IN, 1 = GIVEN_OUT
const swap_kind = 0;

const swap_struct = {
    poolId: swap["poolId"],
    kind: swap_kind,
    assetIn: web3.utils.toChecksumAddress(swap["assetIn"]),
    assetOut: web3.utils.toChecksumAddress(swap["assetOut"]),
    amount: BigNumber(swap["amount"] * Math.pow(10, token_data[swap["assetIn"]]["decimals"])).toString(),
    userData: '0x'
};

const fund_struct = {
    sender: web3.utils.toChecksumAddress(fund_settings["sender"]),
    fromInternalBalance: fund_settings["fromInternalBalance"],
    recipient: web3.utils.toChecksumAddress(fund_settings["recipient"]),
    toInternalBalance: fund_settings["toInternalBalance"]
};

const token_limit = BigNumber((token_data[swap["assetIn"]]["limit"]) * Math.pow(10, token_data[swap["assetIn"]]["decimals"])).toString();

const single_swap_function = contract_vault.methods.swap(
    swap_struct,
    fund_struct,
    token_limit,
    deadline.toString()
);

async function buildAndSend() {
    var gas_estimate;
    try {
        gas_estimate = await single_swap_function.estimateGas();
    }
    catch(err) {
        gas_estimate = 100000;
        console.log("Failed to estimate gas, attempting to send with", gas_estimate, "gas limit...");
    }

    const tx_object = {
        'chainId':  chain_id,
        'gas':      web3.utils.toHex(gas_estimate),
        'gasPrice': web3.utils.toHex(web3.utils.toWei(gas_price,'gwei')),
        'nonce':    await web3.eth.getTransactionCount(address),
        'data':     single_swap_function.encodeABI(),
        'to':       address_vault
    };

    const tx = new Tx(tx_object);
    const signed_tx = await web3.eth.accounts.signTransaction(tx_object, private_key)
                        .then(signed_tx => web3.eth.sendSignedTransaction(signed_tx['rawTransaction']));
    console.log("Sending transaction...");
    const tx_hash = signed_tx["logs"][0]["transactionHash"];
    const url = block_explorer_url + "tx/" + tx_hash;
    open(url);
}
buildAndSend();
