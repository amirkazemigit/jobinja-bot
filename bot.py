import os, time, re, requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

MAX_PAGES = int(os.getenv("MAX_PAGES", "1"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "25"))
SLEEP_BETWEEN_MSGS = float(os.getenv("SLEEP_BETWEEN_MSGS", "0.2"))

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (Linux; Android 10; SM-G973F) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0 Mobile Safari/537.36")

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
    "Referer": "https://jobinja.ir/",
    "Upgrade-Insecure-Requests": "1",
}

def make_session(ua):
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.6,
                    status_forcelist=[429,500,502,503,504],
                    allowed_methods={"GET","POST"}, raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    h = dict(BASE_HEADERS)
    h["User-Agent"] = ua
    s.headers.update(h)
    return s

def send_message(text, session):
    try:
        r = session.post(TG_API, data={
            "chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True
        }, timeout=30)
        # print("TG:", r.status_code, r.text)  # در صورت نیاز باز کن
    except Exception as e:
        print("TG error:", e)

def to_hashtag(t):
    t = re.sub(r"\s+", "_", t.strip())
    t = re.sub(r"[^\w\u0600-\u06FF_]", "", t)
    return f"#{t}" if t and not t.startswith("#") else (t if t else "")

def scrape_with_session(sess, max_pages):
    all_jobs = []
    # 1) گرفتن کوکی اولیه
    try:
        sess.get("https://jobinja.ir/", timeout=30)
    except Exception as e:
        print("Warmup error:", e)

    for page in range(1, max_pages + 1):
        url = f"https://jobinja.ir/jobs?page={page}"
        r = sess.get(url, timeout=30)
        print(f"[FETCH] {url} -> {r.status_code}, len={len(r.text)}")
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.o-listView__item")
        print(f"[PARSE] found cards: {len(cards)}")

        if not cards:
            # لاگ پیش‌نمایش برای دیباگ
            preview = r.text[:400].replace("\n", " ")
            print("[PREVIEW]", preview)
            break

        for card in cards:
            a = card.select_one("a.c-jobListView__title")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://jobinja.ir" + href

            tag_texts = [el.get_text(strip=True)
                         for el in card.select(".c-jobListView__attrs a, .c-jobListView__attrs li a")]
            tags = []
            for t in tag_texts:
                h = to_hashtag(t)
                if h and h not in tags:
                    tags.append(h)

            if title and href:
                all_jobs.append({"title": title, "link": href, "tags": tags})
    return all_jobs

def fetch_jobs_resilient(max_pages=1):
    # تلاش اول: دسکتاپ
    sess = make_session(UA_DESKTOP)
    jobs = scrape_with_session(sess, max_pages)
    if jobs:
        return jobs
    # تلاش دوم: موبایل
    print("[RETRY] switching to mobile UA")
    sess = make_session(UA_MOBILE)
    jobs = scrape_with_session(sess, max_pages)
    return jobs

if __name__ == "__main__":
    jobs = fetch_jobs_resilient(MAX_PAGES)
    if not jobs:
        # پیام کوتاه به تلگرام، لاگ کامل در Actions چاپ شده
        with requests.Session() as s:
            send_message("⚠️ آگهی‌ای پیدا نشد یا دسترسی محدود شد.", s)
    else:
        with requests.Session() as s:
            sent = 0
            for j in jobs:
                if sent >= MAX_ITEMS:
                    break
                tag_line = " ".join(j["tags"][:4]) if j["tags"] else ""
                msg = f"{j['title']}\n{j['link']}"
                if tag_line:
                    msg += f"\n{tag_line}"
                send_message(msg, s)
                sent += 1
                time.sleep(SLEEP_BETWEEN_MSGS)
        print(f"Sent {sent} items.")
