import os, requests, json, time
from bs4 import BeautifulSoup

TOKEN = os.getenv("8254554742:AAFgBihgyEHXHjx2IA0ndmta_kHsgqEtPUU")
CHAT_ID = os.getenv("@karopeydakon")  # @channelusername یا -100...
SEEN_FILE = "seen.json"

URL = "https://jobinja.ir/jobs?filters%5Bkeywords%5D%5B0%5D=python"  # جستجو برای Python

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def get_latest_jobs():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for a in soup.select("a.c-jobListView__titleLink"):
        title = a.get_text(strip=True)
        link = "https://jobinja.ir" + a["href"]
        jobs.append((title, link))
    return jobs

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}
    requests.post(url, data=data)

def main():
    seen = load_seen()
    jobs = get_latest_jobs()
    new_seen = set(seen)
    for title, link in jobs[:5]:  # فقط ۵ تای اول برای نمونه
        if link not in seen:
            msg = f"📝 {title}\n{link}"
            send_to_telegram(msg)
            new_seen.add(link)
            time.sleep(2)
    save_seen(new_seen)

if __name__ == "__main__":
    main()
