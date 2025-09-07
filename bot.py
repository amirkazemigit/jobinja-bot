import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://jobinja.ir/",
}

def send_message(text: str):
    requests.post(TG_API, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }, timeout=30)

def fetch_jobs(keyword="python", limit=5):
    url = f"https://jobinja.ir/jobs?filters%5Bkeywords%5D%5B%5D={keyword}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for a in soup.select("a.c-jobListView__title"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if href.startswith("/"):
            href = "https://jobinja.ir" + href
        if title and href:
            jobs.append(f"{title}\n{href}")
        if len(jobs) >= limit:
            break

    # لاگ کوچک برای دیباگ
    if not jobs:
        preview = r.text[:600].replace("\n", " ")
        send_message("⚠️ شغلی پیدا نشد. شاید سایت محتوای خالی داده یا مسدود کرده.\n"
                     "وضعیت: " + str(r.status_code) + "\nپیش‌نمایش HTML: " + preview)

    return jobs

if __name__ == "__main__":
    jobs = fetch_jobs()
    if not jobs:
        # پیام دیباگ بالا ارسال شده
        pass
    else:
        for j in jobs:
            send_message(j)
