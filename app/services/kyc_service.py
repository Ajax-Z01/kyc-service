import hashlib
import os
from datetime import datetime
from google.cloud import firestore
from aiofiles import open as aio_open

TEMP_FOLDER = "temp"
os.makedirs(TEMP_FOLDER, exist_ok=True)

db = firestore.Client()

async def save_document(wallet_address: str, file):
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"{file_hash}_{file.filename}"

    async with aio_open(f"{TEMP_FOLDER}/{file_name}", "wb") as f:
        await f.write(content)

    doc_ref = db.collection("documents").document()
    doc_ref.set({
        "walletAddress": wallet_address,
        "fileName": file.filename,
        "fileHash": file_hash,
        "status": "Draft",
        "tokenId": None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    })

    return doc_ref.id
