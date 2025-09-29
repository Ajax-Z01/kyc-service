import os
from dotenv import load_dotenv

load_dotenv()  # harus ini dulu sebelum Firestore

from fastapi import FastAPI
from app.api import documents

app = FastAPI(title="KYC Service")
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

@app.get("/")
async def root():
    return {"message": "KYC Service is running"}
