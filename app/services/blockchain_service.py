from web3 import Web3
import json
import os

# --------- konfigurasi Web3 ---------
RPC_URL = os.getenv("ETH_RPC_URL")  # misal Ganache atau testnet
PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY")  # kunci admin KYC
CONTRACT_ADDRESS = os.getenv("KYC_CONTRACT_ADDRESS")
ABI_PATH = "app/contracts/KYCRegistry.sol/KYCRegistry.json"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# load ABI
with open(ABI_PATH) as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=contract_abi)

# --------- helper function ---------
def mint_document(to_address: str, file_hash: str, token_uri: str):
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.verifyAndMint(
        Web3.toChecksumAddress(to_address),
        file_hash,
        token_uri
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': w3.to_wei('10', 'gwei')
    })

    signed_txn = account.sign_transaction(txn)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def get_document_status(token_id: int):
    return contract.functions.getStatus(token_id).call()

def sign_document(token_id: int):
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.signDocument(token_id).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.to_wei('10', 'gwei')
    })

    signed_txn = account.sign_transaction(txn)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt
