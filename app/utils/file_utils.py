import os
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image

async def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    print(f"[DEBUG] Extracting text from: {file_path} (ext: {ext})")

    if ext == ".pdf":
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            print(f"[DEBUG] PDF page {i} text length: {len(page_text)}")
            text += page_text
    elif ext in [".png", ".jpg", ".jpeg"]:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            print(f"[DEBUG] Plain text length: {len(text)}")
            print(f"[DEBUG] Plain text preview: {text[:200]}")

    return text
