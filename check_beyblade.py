import os
from bs4 import BeautifulSoup
import requests

TARGET_KEYWORD = "爆旋陀螺"
URLS = [
    "https://www.toysrus.com.hk/zh-hk/beyblade/",
    "https://www.hobbylandeshop.com/product-category/nproduct_booking",
]

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

found_urls = []

for url in URLS:
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = "utf-8"

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()

            if TARGET_KEYWORD in page_text:
                print(f"[FOUND] {TARGET_KEYWORD} detected at: {url}")
                found_urls.append(url)
            else:
                print(f"[NOT FOUND] {TARGET_KEYWORD} not present at: {url}")
        else:
            print(f"[ERROR] Failed to fetch {url} (Status: {response.status_code})")

    except Exception as e:
        print(f"[EXCEPTION] Could not reach {url}: {e}")

# Send Discord notification if keyword is found on any site
if found_urls and WEBHOOK_URL:
    links_str = "\n".join(found_urls)
    message = (
        f"🎯 **Found '{TARGET_KEYWORD}'!**\n"
        f"The term was detected on the following page(s):\n{links_str}"
    )
    requests.post(WEBHOOK_URL, json={"content": message})
