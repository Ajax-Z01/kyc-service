from fastapi import APIRouter, UploadFile, Form, HTTPException
from app.services.kyc_service import save_document, get_all_documents, get_document, get_document_logs
from app.models.document import DocumentResponse
from typing import List

router = APIRouter()


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    wallet_address: str = Form(...),
    file: UploadFile = None
):
    document = await save_document(wallet_address, file)
    return document

@router.get("/", response_model=List[DocumentResponse])
async def read_all_documents():
    return get_all_documents()

@router.get("/{document_id}", response_model=DocumentResponse)
async def read_document(document_id: str):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/logs")
async def read_document_logs(document_id: str):
    logs = get_document_logs(document_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this document")
    return logs