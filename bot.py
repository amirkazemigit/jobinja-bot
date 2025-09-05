import os, requests, sys

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def main():
    if not TOKEN or not CHAT_ID:
        print("MISSING_ENV", bool(TOKEN), bool(CHAT_ID))
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": "✅ Hello from GitHub Actions (test)"}
    try:
        r = requests.post(url, data=data, timeout=20)
        print("Status:", r.status_code)
        print("Response:", r.text)
        r.raise_for_status()
    except Exception as e:
        print("EXCEPTION:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
