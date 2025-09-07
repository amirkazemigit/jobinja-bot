import os
import time
import re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------ تنظیمات عمومی ------
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# فقط صفحهٔ اول
MAX_PAGES = int(os.getenv("MAX_PAGES", "1"))
# حداکثر تعداد آگهی که در هر اجرا می‌فرستی (برای کنترل حجم)
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "25"))
# مکث بین پیام‌ها (ثانیه)
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

# ------ ابزارهای کمکی ------
def make_session():
    """Session با Retry و Timeout منطقی."""
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
    try:
        session.post(
            TG_API,
            data={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True},
            timeout=30,
        )
    except Exception as e:
        # در سکوت رد نکن؛ اگر خواستی می‌تونی به لاگ GitHub Actions هم چاپ کنی
        print("Telegram send error:", e)

def to_hashtag(text: str) -> str:
    """
    متن فارسی دسته‌بندی را به هشتگ تمیز تبدیل می‌کند.
    مثال: 'برنامه نویسی' -> '#برنامه_نویسی'
    """
    t = text.strip()
    t = re.sub(r"\s+", "_", t)                          # فاصله → زیرخط
    t = re.sub(r"[^\w\u0600-\u06FF_]", "", t)           # حذف کاراکترهای اضافی
    if not t:
        return ""
    if not t.startswith("#"):
        t = "#" + t
    return t

# ------ هستهٔ اسکرپ ------
def fetch_jobs_first_pages(max_pages=1, session=None):
    """
    از /jobs صفحه به صفحه می‌خواند (پیش‌فرض فقط صفحهٔ اول)
    خروجی: [{title, link, tags: [#tag,...]}]
    """
    session = session or make_session()
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = f"https://jobinja.ir/jobs?page={page}"
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
        except Exception as e:
            print("HTTP error:", e)
            break

        if r.status_code != 200:
            print("Non-200:", r.status_code, "for", url)
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.o-listView__item")
        if not cards:
            # صفحه خالی/ساختار عوض شده یا مسدود شد
            break

        f
