import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_test_message():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": "✅ Hello from GitHub Actions! رباتت درست کار می‌کنه 🚀"
    }
    r = requests.post(url, data=data)
    print("Status:", r.status_code)
    print("Response:", r.text)

if __name__ == "__main__":
    send_test_message()
