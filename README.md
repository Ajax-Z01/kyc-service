# KYC Service

KYC Service adalah backend microservice untuk memproses KYC (Know Your Customer) dan dokumen terkait.  
Service ini dapat menerima dokumen dari frontend/trade-chain, menyimpan metadata di Firestore, serta mempersiapkan integrasi dengan blockchain untuk status NFT.

## Fitur

- Upload dokumen KYC
- Simpan metadata dokumen di Firestore
- Temp storage lokal untuk dokumen sebelum diverifikasi
- Siap untuk integrasi dengan smart contract (NFT)

## Struktur Folder

```

kyc-service/
├─ app/
│  ├─ api/            # Router FastAPI
│  ├─ services/       # Logika backend & blockchain service
│  ├─ models/         # Model data
├─ account/           # Service Account JSON Firestore
├─ temp/              # Penyimpanan sementara dokumen
├─ main.py            # Entry point FastAPI
├─ .env               # Environment variables
├─ requirements.txt
├─ README.md

````

## Setup

1. Buat virtual environment dan install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
````

2. Tambahkan file service account Firestore di `account/serviceAccount.json`.
3. Buat `.env` dengan:

```
GOOGLE_APPLICATION_CREDENTIALS=account/serviceAccount.json
```

4. Jalankan server FastAPI:

```bash
uvicorn app.main:app --reload
```

5. Akses endpoint:

* Root: `GET /` → test service
* Documents: `POST /documents` → upload dokumen

## Catatan

* Dokumen masih disimpan sementara di folder `temp/`.
* Metadata dokumen tersimpan di Firestore.
* Siap dikembangkan untuk interaksi blockchain (NFT verification).

```