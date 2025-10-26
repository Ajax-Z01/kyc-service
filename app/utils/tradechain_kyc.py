from typing import Optional, Dict
import requests
import os

TRADECHAIN_BACKEND_URL = os.getenv("TRADECHAIN_BACKEND_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")


def update_kyc_internal(
    token_id: str,
    status: Optional[str] = None,
    signature: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    tx_hash: Optional[str] = None,
    remarks: Optional[str] = None,
) -> bool:
    """
    Kirim update internal KYC ke TradeChain backend.
    Tidak perlu model lokal karena data KYC ada di Firestore TradeChain.
    """
    if not TRADECHAIN_BACKEND_URL or not INTERNAL_API_KEY:
        print("❌ Missing TRADECHAIN_BACKEND_URL or INTERNAL_API_KEY")
        return False

    url = f"{TRADECHAIN_BACKEND_URL.rstrip('/')}/kyc/internal/{token_id}/status"
    payload: Dict = {}
    if status:
        payload["status"] = status
    if signature:
        payload["signature"] = signature
    if reviewed_by:
        payload["reviewedBy"] = reviewed_by
    if tx_hash:
        payload["txHash"] = tx_hash
    if remarks:
        payload["remarks"] = remarks

    try:
        resp = requests.patch(
            url,
            json=payload,
            headers={
                "x-internal-key": INTERNAL_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=10
        )
        if resp.status_code in (200, 201):
            print(f"✅ KYC {token_id} updated internally")
            return True
        else:
            print(f"⚠️ Failed to update KYC: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating KYC: {e}")
        return False
