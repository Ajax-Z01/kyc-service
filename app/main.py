import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents

app = FastAPI(title="KYC Service")
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "KYC Service is running"}

@app.post("/mock-verification")
async def mock_verification(
    file: UploadFile = File(...),
    x_encryption_key: str = Header(None)
):
    content = await file.read()

    print(f"[MOCK] Received file: {file.filename}, size: {len(content)} bytes")
    print(f"[MOCK] Encryption Key: {x_encryption_key}")

    # Contoh respons mock
    return JSONResponse({
        "status": "Verified",
        "message": "Mock verification successful",
        "file_name": file.filename
    })