import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests

TARGET_KEYWORD = "Takara Tomy"
URLS = [
    "https://www.toysrus.com.hk/zh-hk/beyblade/",
    "https://www.hobbylandeshop.com/product-category/nproduct_booking",
]

# Email Configuration from Environment Variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")  # Gmail App Password
RECEIVER_EMAIL = "yws1024@gmail.com"


def send_email(found_urls):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[EMAIL ERROR] SENDER_EMAIL or SENDER_PASSWORD secret missing.")
        return

    links_str = "\n".join(found_urls)
    subject = f"🎯 Found '{TARGET_KEYWORD}' Stock Alert!"
    body = (
        f"The keyword '{TARGET_KEYWORD}' was detected on the following page(s):\n\n"
        f"{links_str}\n\n"
        f"Check them quickly before stock runs out!"
    )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        # Connect to Gmail SMTP Server (SSL on port 465)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL SUCCESS] Alert email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")


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
            print(
                f"[ERROR] Failed to fetch {url} (Status: {response.status_code})"
            )

    except Exception as e:
        print(f"[EXCEPTION] Could not reach {url}: {e}")

# Send Email if keyword found
if found_urls:
    send_email(found_urls)
