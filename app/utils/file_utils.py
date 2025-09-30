import os
import hashlib
from aiofiles import open as aio_open

TEMP_FOLDER = "temp"
os.makedirs(TEMP_FOLDER, exist_ok=True)

async def save_temp_file(file):
    """
    Simpan file sementara dan hitung hash-nya.
    """
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"{file_hash}_{file.filename}"

    file_path = os.path.join(TEMP_FOLDER, file_name)
    async with aio_open(file_path, "wb") as f:
        await f.write(content)

    return file_path, file_hash
