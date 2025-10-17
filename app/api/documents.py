from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from app.services.kyc_service import (
    save_document,
    get_all_documents,
    get_document,
    get_document_logs
)
from app.services.blockchain_service import (
    review_document_onchain,
    sign_document_onchain,
    add_minter
)
from app.models.document import DocumentResponse

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
async def review_document(document_id: str):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "Draft":
        raise HTTPException(status_code=400, detail="Only Draft documents can be reviewed")

    # Panggil blockchain service untuk review (update status on-chain)
    review_document_onchain(document.token_id or 0)

    return JSONResponse({"status": "Reviewed", "document_id": document_id})


# ---------------- Sign document ----------------
@router.post("/{document_id}/sign")
async def sign_document(document_id: str):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "Reviewed":
        raise HTTPException(status_code=400, detail="Only Reviewed documents can be signed")

    # Panggil blockchain service untuk sign (update status on-chain)
    tx_receipt = sign_document_onchain(document.token_id or 0)

    return JSONResponse({
        "status": "Signed",
        "document_id": document_id,
        "tx_hash": tx_receipt.transactionHash.hex()
    })

# ---------------- Add Minter ----------------
@router.post("/minters/add")
async def add_minter_endpoint(minter_address: str = Form(...)):
    try:
        receipt = add_minter(minter_address)
        return JSONResponse({
            "status": "success",
            "minter_address": minter_address,
            "tx_hash": receipt.transactionHash.hex()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))