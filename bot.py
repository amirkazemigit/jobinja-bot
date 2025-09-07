import os
import time
import re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # عددی! برای کانال معمولاً منفی است
TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# فقط صفحه‌ی اول، ضداسپم و تمیز
MAX_PAGES = int(os.getenv("MAX_PAGES", "1"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "25"))
SLEEP_BETWEEN_MSGS = float(os.getenv("SLEEP_BETWEEN_MSGS", "0.2"))

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

def make_session():
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods={"GET", "POST"},
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def send_message(text: str, session: requests.Session):
    r = session.post(
        TG_API,
        data={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True},
        timeout=30,
    )
    # برای دیباگ اولیه، خط زیر را می‌توانی کامنت/آنکامنت کنی:
    # print("TG:", r.status_code, r.text)

def to_hashtag(t: str) -> str:
    t = t.strip()
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^\w\u0600-\u06FF_]", "", t)
    return f"#{t}" if t and not t.startswith("#") else (t if t else "")

def fetch_jobs_first_pages(max_pages=1, session=None):
    session = session or make_session()
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = f"https://jobinja.ir/jobs?page={page}"
        r = session.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.o-listView__item")
        if not cards:
            break

        for card in cards:
            a = card.select_one("a.c-jobListView__title")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://jobinja.ir" + href

            tag_texts = [el.get_text(strip=True) for el in card.select(".c-jobListView__attrs a, .c-jobListView__attrs li a")]
            tags = []
            for t in tag_texts:
                h = to_hashtag(t)
                if h and h not in tags:
                    tags.append(h)

            if title and href:
                all_jobs.append({"title": title, "link": href, "tags": tags})
    return all_jobs

if __name__ == "__main__":
    sess = make_session()
    jobs = fetch_jobs_first_pages(max_pages=MAX_PAGES, session=sess)

    if not jobs:
        send_message("⚠️ آگهی‌ای پیدا نشد یا دسترسی محدود شد.", sess)
    else:
        sent = 0
        for j in jobs:
            if sent >= MAX_ITEMS:
                break
            tag_line = " ".join(j["tags"][:4]) if j["tags"] else ""
            msg = f"{j['title']}\n{j['link']}"
            if tag_line:
                msg += f"\n{tag_line}"
            send_message(msg, sess)
            sent += 1
            time.sleep(SLEEP_BETWEEN_MSGS)
        print(f"Sent {sent} items.")
