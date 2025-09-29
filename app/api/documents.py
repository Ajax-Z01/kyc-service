from fastapi import APIRouter, UploadFile, Form
from app.services.kyc_service import save_document

router = APIRouter()

@router.post("/")
async def upload_document(
    wallet_address: str = Form(...),
    file: UploadFile = None
):
    document_id = await save_document(wallet_address, file)
    return {"message": "Document uploaded", "document_id": document_id}
