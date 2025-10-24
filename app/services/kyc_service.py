import os
import hashlib
from datetime import datetime
from typing import List, Callable, Optional
import aiofiles
from google.cloud import firestore

from app.services.blockchain_service import mint_document, review_document_onchain, sign_document_onchain
from app.utils.file_utils import extract_text
from app.utils.ktp_parser import parse_ktp
from app.utils.verification import verify_document_advanced
from app.models.document import DocumentResponse
from app.utils.crypto_utils import encrypt_file
from app.services.openai_service import analyze_document_with_ai
from app.utils.tradechain_notifier import send_tradechain_notification

db = firestore.Client()


# ---------------- Upload dokumen dari Trade Chain ----------------
async def save_document_from_trade_chain(
    wallet_address: str,
    token_id: int,
    file,
    parser_hook: Optional[Callable[[str], dict]] = None,
    ai_hook: Optional[Callable[[str], dict]] = None
):
    """
    Simpan dokumen yang berasal dari sistem trade-chain.
    - Tidak melakukan minting lagi
    - Menyimpan token_id yang sudah ada
    - OCR + optional parser/AI
    """
    TEMP_FOLDER = "temp"
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # --- Simpan file sementara ---
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"{file_hash}_{file.filename}"
    file_path = f"{TEMP_FOLDER}/{file_name}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    now = datetime.utcnow()

    # --- Simpan metadata awal ---
    doc_ref = db.collection("documents").document()
    metadata = {
        "walletAddress": wallet_address,
        "fileName": file.filename,
        "fileHash": file_hash,
        "status": "Draft",
        "tokenId": token_id,
        "createdAt": now,
        "updatedAt": now
    }
    doc_ref.set(metadata)

    # --- 🔐 Enkripsi file ---
    encrypted_path, encryption_key = encrypt_file(file_path)

    # --- 📝 Ekstraksi teks ---
    text = await extract_text(file_path)

    # --- Hapus file plaintext ---
    os.remove(file_path)

    # --- Parsing optional ---
    parsed_fields = parser_hook(text) if parser_hook else {}
    ai_fields = ai_hook(text) if ai_hook else {}

    # --- Simpan log OCR + hasil parsing ---
    log_ref = db.collection("document_logs").document()
    log_ref.set({
        "documentId": doc_ref.id,
        "ocrText": text,
        "parsedFieldsLocal": parsed_fields,
        "parsedFieldsAI": ai_fields,
        "createdAt": datetime.utcnow()
    })

    # --- Ambil snapshot terakhir ---
    doc_snapshot = doc_ref.get().to_dict()

    return {
        "id": doc_ref.id,
        "wallet_address": doc_snapshot.get("walletAddress", ""),
        "file_name": doc_snapshot.get("fileName", ""),
        "file_hash": doc_snapshot.get("fileHash", ""),
        "status": doc_snapshot.get("status", "Received"),
        "token_id": doc_snapshot.get("tokenId"),
        "created_at": doc_snapshot.get("createdAt", now),
        "updated_at": doc_snapshot.get("updatedAt", now)
    }


# ---------------- Upload dan buat dokumen status Draft ----------------
async def save_document(
    wallet_address: str,
    file,
    parser_hook: Optional[Callable[[str], dict]] = None,
    ai_hook: Optional[Callable[[str], dict]] = None
) -> DocumentResponse:
    """
    parser_hook: callable yang menerima teks dan mengembalikan dict parsed fields
    ai_hook: callable yang menerima teks dan mengembalikan dict hasil AI
    """

    TEMP_FOLDER = "temp"
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # --- Simpan file sementara ---
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"{file_hash}_{file.filename}"
    file_path = f"{TEMP_FOLDER}/{file_name}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    now = datetime.utcnow()

    # --- Simpan metadata awal (Draft) ---
    doc_ref = db.collection("documents").document()
    metadata = {
        "walletAddress": wallet_address,
        "fileName": file.filename,
        "fileHash": file_hash,
        "status": "Draft",
        "tokenId": None,
        "createdAt": now,
        "updatedAt": now
    }
    doc_ref.set(metadata)

    # --- 🔐 Enkripsi file ---
    encrypted_path, encryption_key = encrypt_file(file_path)

    # --- 📝 Ekstraksi teks ---
    text = await extract_text(file_path)

    # --- Hapus file plaintext ---
    os.remove(file_path)

    # --- Parsing optional ---
    parsed_fields = parser_hook(text) if parser_hook else {}
    ai_fields = ai_hook(text) if ai_hook else {}

    # --- Simpan log OCR + hasil parsing ---
    log_ref = db.collection("document_logs").document()
    log_ref.set({
        "documentId": doc_ref.id,
        "ocrText": text,
        "parsedFieldsLocal": parsed_fields,
        "parsedFieldsAI": ai_fields,
        "createdAt": datetime.utcnow()
    })

    # ---------------- Mint dokumen di blockchain ----------------
    try:
        token_id = mint_document(
            to_address=wallet_address,
            file_hash=file_hash,
            token_uri=f"ipfs://{file_hash}"
        )
        doc_ref.update({"tokenId": token_id})
    except Exception as e:
        print(f"⚠️ Mint failed: {e}")

    # Ambil snapshot terakhir
    doc_snapshot = doc_ref.get().to_dict()
    return DocumentResponse(
        id=doc_ref.id,
        wallet_address=doc_snapshot.get("walletAddress", ""),
        file_name=doc_snapshot.get("fileName", ""),
        file_hash=doc_snapshot.get("fileHash", ""),
        status=doc_snapshot.get("status", "Draft"),
        token_id=doc_snapshot.get("tokenId"),
        created_at=doc_snapshot.get("createdAt", now),
        updated_at=doc_snapshot.get("updatedAt", now)
    )


# ---------------- Review Dokumen (Admin) ----------------
def review_document(document_id: str) -> bool:
    doc_ref = db.collection("documents").document(document_id)
    doc_snapshot = doc_ref.get()
    if not doc_snapshot.exists:
        return False

    data = doc_snapshot.to_dict()

    # Mint token jika belum pernah di-mint
    if not data.get("tokenId"):
        token_id = mint_document(
            to_address=data["walletAddress"],
            file_hash=data["fileHash"],
            token_uri=f"ipfs://{data['fileHash']}"
        )
        doc_ref.update({"tokenId": token_id})
        data["tokenId"] = token_id

    # Panggil fungsi review di blockchain
    review_document_onchain(data["tokenId"])

    # ✅ Update status Firestore
    doc_ref.update({
        "status": "Reviewed",
        "updatedAt": datetime.utcnow()
    })

    # 🔔 Kirim notifikasi ke TradeChain backend
    send_tradechain_notification(
        user_id=data.get("walletAddress", ""),
        executor_id="kyc_service",
        notif_type="system",
        title="KYC Review Completed",
        message=f"Your document {data.get('fileName', '')} has been reviewed successfully.",
        extra_data={
            "documentId": document_id,
            "tokenId": data.get("tokenId"),
            "status": "Reviewed"
        }
    )

    return True


# ---------------- Sign Dokumen (Admin) ----------------
def sign_document(document_id: str) -> bool:
    doc_ref = db.collection("documents").document(document_id)
    doc_snapshot = doc_ref.get()
    if not doc_snapshot.exists:
        return False

    data = doc_snapshot.to_dict()
    token_id = data.get("tokenId")
    if not token_id:
        return False

    # Panggil blockchain untuk sign
    sign_document_onchain(token_id)

    # ✅ Update status Firestore
    doc_ref.update({
        "status": "Signed",
        "updatedAt": datetime.utcnow()
    })
    
    # 🔔 Kirim notifikasi ke TradeChain backend
    send_tradechain_notification(
        user_id=data.get("walletAddress", ""),
        executor_id="kyc_service",
        notif_type="system",
        title="KYC Document Signed",
        message=f"Your document {data.get('fileName', '')} has been signed successfully.",
        extra_data={
            "documentId": document_id,
            "tokenId": token_id,
            "status": "Signed"
        }
    )
    
    return True


# ---------------- Getter ----------------
def get_document(document_id: str) -> Optional[DocumentResponse]:
    doc_ref = db.collection("documents").document(document_id)
    doc_snapshot = doc_ref.get()
    if not doc_snapshot.exists:
        return None
    data = doc_snapshot.to_dict()
    return DocumentResponse(
        id=document_id,
        wallet_address=data.get("walletAddress", ""),
        file_name=data.get("fileName", ""),
        file_hash=data.get("fileHash", ""),
        status=data.get("status", "Draft"),
        token_id=data.get("tokenId"),
        created_at=data.get("createdAt", datetime.utcnow()),
        updated_at=data.get("updatedAt", datetime.utcnow())
    )


def get_all_documents() -> List[DocumentResponse]:
    snapshots = db.collection("documents").stream()
    documents = []
    for doc in snapshots:
        data = doc.to_dict()
        documents.append(
            DocumentResponse(
                id=doc.id,
                wallet_address=data.get("walletAddress", ""),
                file_name=data.get("fileName", ""),
                file_hash=data.get("fileHash", ""),
                status=data.get("status", "Draft"),
                token_id=data.get("tokenId"),
                created_at=data.get("createdAt", datetime.utcnow()),
                updated_at=data.get("updatedAt", datetime.utcnow())
            )
        )
    return documents


def get_document_logs(document_id: str) -> List[dict]:
    snapshots = db.collection("document_logs") \
                  .where("documentId", "==", document_id) \
                  .order_by("createdAt") \
                  .stream()
    logs = []
    for log in snapshots:
        data = log.to_dict()
        logs.append({
            "id": log.id,
            "ocrText": data.get("ocrText", ""),
            "parsedFieldsLocal": data.get("parsedFieldsLocal", {}),
            "parsedFieldsAI": data.get("parsedFieldsAI", {}),
            "verificationLocal": data.get("verificationLocal", ""),
            "verificationAI": data.get("verificationAI", ""),
            "createdAt": data.get("createdAt", datetime.utcnow())
        })
    return logs
