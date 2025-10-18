from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

async def analyze_document_with_ai(text: str) -> dict:
    prompt = f"""
    Kamu adalah sistem verifikasi dokumen KTP.
    Ekstrak semua field penting (nama, NIK, alamat, tanggal lahir, dll) dan berikan status:
    'Verified' atau 'Rejected'. Berikan output dalam JSON:
    {{ "status": "...", "parsedFields": {{...}} }}
    Teks dokumen: {text[:8000]}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(response.choices[0].message.content)
