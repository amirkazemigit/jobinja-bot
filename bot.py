import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
    requests.post(url, data=data)

def fetch_jobs():
    url = "https://jobinja.ir/jobs?filters%5Bkeywords%5D%5B%5D=python"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []
    for job in soup.select("div.o-listView__itemHeading a.c-jobListView__title"):
        title = job.text.strip()
        link = "https://jobinja.ir" + job["href"]
        jobs.append(f"{title}\n{link}")
    return jobs[:5]  # فقط ۵ تا آگهی اول

if __name__ == "__main__":
    jobs = fetch_jobs()
    if not jobs:
        send_message("❌ شغلی پیدا نشد")
    else:
        for job in jobs:
            send_message(job)
