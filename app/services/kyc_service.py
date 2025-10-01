from datetime import datetime
from app.services.blockchain_service import sign_document
from app.utils.file_utils import extract_text
from app.utils.ktp_parser import parse_ktp
from app.utils.verification import verify_document_advanced
from google.cloud import firestore
from app.models.document import DocumentResponse
from typing import List, Optional

db = firestore.Client()


async def save_document(wallet_address: str, file) -> DocumentResponse:
    import hashlib, os
    from aiofiles import open as aio_open

    TEMP_FOLDER = "temp"
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # --- Save file to temp ---
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"{file_hash}_{file.filename}"
    file_path = f"{TEMP_FOLDER}/{file_name}"

    async with aio_open(file_path, "wb") as f:
        await f.write(content)

    # --- Save document metadata ---
    doc_ref = db.collection("documents").document()
    now = datetime.utcnow()
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

    # --- Extract text ---
    text = await extract_text(file_path)

    # --- Parse KTP fields ---
    parsed_fields = parse_ktp(text)

    # --- Verification ---
    verification_result = verify_document_advanced(parsed_fields)

    # --- Save log with parsed fields ---
    log_ref = db.collection("document_logs").document()
    log_ref.set({
        "documentId": doc_ref.id,
        "ocrText": text,
        "parsedFields": parsed_fields,
        "verificationResult": verification_result,
        "status": "Draft",
        "createdAt": datetime.utcnow()
    })

    # --- Update document status ---
    if verification_result == "Verified":
        doc_ref.update({"status": "Verified", "updatedAt": datetime.utcnow()})
        token_id = sign_document(doc_ref.id)
        doc_ref.update({"status": "Signed", "tokenId": token_id, "updatedAt": datetime.utcnow()})
    else:
        doc_ref.update({"status": "Rejected", "updatedAt": datetime.utcnow()})

    # --- Return DocumentResponse ---
    doc_snapshot = doc_ref.get().to_dict()
    return DocumentResponse(
        id=doc_ref.id,
        wallet_address=doc_snapshot.get("walletAddress", ""),
        file_name=doc_snapshot.get("fileName", ""),
        file_hash=doc_snapshot.get("fileHash", ""),
        status=doc_snapshot.get("status", "Draft"),
        token_id=doc_snapshot.get("tokenId"),
        created_at=doc_snapshot.get("createdAt", datetime.utcnow()),
        updated_at=doc_snapshot.get("updatedAt", datetime.utcnow())
    )


def get_document(document_id: str) -> Optional[DocumentResponse]:
    """Ambil metadata dokumen berdasarkan ID"""
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
    """Ambil semua dokumen dari Firestore"""
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
    """Ambil semua log OCR untuk dokumen tertentu"""
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
            "parsedFields": data.get("parsedFields", {}),
            "verificationResult": data.get("verificationResult", "Draft"),
            "createdAt": data.get("createdAt", datetime.utcnow())
        })
    return logs
