import aiohttp

async def send_for_verification(file_path: str, encryption_key: bytes) -> str:
    url = "http://localhost:8000/mock-verification"  # sementara pakai mock lokal
    headers = {"X-Encryption-Key": encryption_key.hex()}

    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            files = {"file": f}
            async with session.post(url, data=files, headers=headers) as resp:
                data = await resp.json()
                return data.get("status", "Unknown")
