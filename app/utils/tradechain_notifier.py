import os
import requests

TRADECHAIN_BACKEND_URL = os.getenv("TRADECHAIN_BACKEND_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def send_tradechain_notification(user_id: str, executor_id: str, notif_type: str, title: str, message: str, extra_data: dict = None):
    """
    Kirim notifikasi ke backend TradeChain (via endpoint internal)
    """
    if not TRADECHAIN_BACKEND_URL or not INTERNAL_API_KEY:
        print("❌ Missing TRADECHAIN_BACKEND_URL or INTERNAL_API_KEY")
        return False

    url = f"{TRADECHAIN_BACKEND_URL.rstrip('/')}/notification/internal"

    payload = {
        "userId": user_id,
        "executorId": executor_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "extraData": extra_data or {},
    }

    try:
        resp = requests.post(url, json=payload, headers={
            "x-internal-key": INTERNAL_API_KEY,
            "Content-Type": "application/json",
        })
        if resp.status_code == 201:
            print(f"✅ Notification sent to TradeChain backend for user {user_id}")
            return True
        else:
            print(f"⚠️ Notification failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False
