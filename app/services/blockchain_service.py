from web3 import Web3
import json
import os

# --------- Konfigurasi Web3 ---------
RPC_URL = os.getenv("ETH_RPC_URL")
PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("KYC_CONTRACT_ADDRESS")
ABI_PATH = "app/contracts/KYCRegistry.sol/KYCRegistry.json"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise RuntimeError("❌ Gagal konek ke RPC, cek ETH_RPC_URL.")

# Load ABI
with open(ABI_PATH) as f:
    artifact = json.load(f)
contract_abi = artifact["abi"]

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=contract_abi
)

# --------- Helpers ---------
def _get_admin_account():
    return w3.eth.account.from_key(PRIVATE_KEY)


def _build_and_send(txn):
    account = _get_admin_account()
    signed = account.sign_transaction(txn)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


# --------- Blockchain Actions ---------
def mint_document(to_address: str, file_hash: str, token_uri: str) -> int:
    """
    Mint dokumen dan ambil tokenId yang dihasilkan.
    """
    account = _get_admin_account()
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.verifyAndMint(
        Web3.to_checksum_address(to_address),
        file_hash,
        token_uri
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 350_000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    # Kirim transaksi
    _build_and_send(txn)

    # Ambil tokenId dari kontrak (hash -> tokenId)
    token_id = contract.functions.getTokenIdByHash(file_hash).call()
    return token_id


def review_document_onchain(token_id: int):
    """
    Admin melakukan review dokumen (Draft -> Reviewed)
    """
    account = _get_admin_account()
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.reviewDocument(token_id).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200_000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    return _build_and_send(txn)


def sign_document_onchain(token_id: int):
    """
    Admin tanda tangan dokumen (Reviewed -> Signed)
    """
    account = _get_admin_account()
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.signDocument(token_id).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200_000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    return _build_and_send(txn)


def get_token_id_by_hash(file_hash: str) -> int:
    """
    Ambil tokenId dari hash dokumen
    """
    return contract.functions.getTokenIdByHash(file_hash).call()


def get_document_status(token_id: int) -> int:
    """
    Ambil status dokumen (0 = Draft, 1 = Reviewed, 2 = Signed)
    """
    return contract.functions.getStatus(token_id).call()


def add_minter(minter_address: str):
    account = _get_admin_account()
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.addMinter(
        Web3.to_checksum_address(minter_address)
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 100_000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    receipt = _build_and_send(txn)
    return receipt
    
