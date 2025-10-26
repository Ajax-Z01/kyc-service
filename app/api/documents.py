from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from app.services.kyc_service import (
    save_document_from_trade_chain,
    save_document,
    get_all_documents,
    get_document,
    get_document_logs,
    review_document,
    sign_document
)
from app.services.blockchain_service import add_minter, is_minter
from app.models.document_model import DocumentResponse

router = APIRouter()

# ---------------- Upload document ----------------
@router.post("/", response_model=DocumentResponse)
async def upload_document(
    wallet_address: str = Form(...),
    file: UploadFile = None
):
    if not file:
        raise HTTPException(status_code=400, detail="File is required")
    document = await save_document(wallet_address, file)
    return document


# ---------------- Upload document from Trade Chain ----------------
@router.post("/trade-chain")
async def upload_trade_chain_document(
    wallet_address: str = Form(...),
    token_id: int = Form(...),
    file: UploadFile = None
):
    result = await save_document_from_trade_chain(
        wallet_address=wallet_address,
        token_id=token_id,
        file=file
    )
    return result


# ---------------- List all documents ----------------
@router.get("/", response_model=List[DocumentResponse])
async def read_all_documents():
    return get_all_documents()


# ---------------- Get document by ID ----------------
@router.get("/{document_id}", response_model=DocumentResponse)
async def read_document(document_id: str):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


# ---------------- Get document logs ----------------
@router.get("/{document_id}/logs")
async def read_document_logs(document_id: str):
    logs = get_document_logs(document_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this document")
    return logs


# ---------------- Review document ----------------
@router.post("/{document_id}/review")
async def review_document_endpoint(document_id: str):
    """
    Review dokumen → update status di blockchain dan Firestore
    """
    success = review_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or failed to review")
    return JSONResponse({"status": "Reviewed", "document_id": document_id})


# ---------------- Sign document ----------------
@router.post("/{document_id}/sign")
async def sign_document_endpoint(document_id: str):
    """
    Sign dokumen → update status di blockchain dan Firestore
    """
    success = sign_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or failed to sign")
    return JSONResponse({"status": "Signed", "document_id": document_id})


# ---------------- Add Minter ----------------
@router.post("/minters/add")
async def add_minter_endpoint(minter_address: str = Form(...)):
    """
    Menambahkan address ke daftar minter contract.
    Hanya admin yang seharusnya boleh memanggil ini.
    """
    try:
        receipt = add_minter(minter_address)
        return JSONResponse({
            "status": "success",
            "minter_address": minter_address,
            "tx_hash": receipt.transactionHash.hex()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add minter: {str(e)}")


# ---------------- Check Is Minter ----------------
@router.get("/minters/{address}")
async def check_is_minter(address: str):
    """
    Mengecek apakah suatu address sudah terdaftar sebagai minter.
    """
    try:
        result = is_minter(address)
        return JSONResponse({
            "address": address,
            "is_minter": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check minter: {str(e)}")
