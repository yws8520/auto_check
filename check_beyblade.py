import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# Update keyword if you are searching for '爆旋陀螺' or 'Takara Tomy'
TARGET_KEYWORD = "BX-53"
URLS = [
    "https://www.toysrus.com.hk/zh-hk/whats-on/new-arrivals/pre-order/",
    "https://www.hobbylandeshop.com/product-category/nproduct_booking",
]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
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
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL SUCCESS] Alert email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")


found_urls = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for url in URLS:
        try:
            page = context.new_page()
            # Fast load state to avoid network tracking timeouts
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Pause briefly to allow basic dynamic elements to populate
            page.wait_for_timeout(3000)

            content = page.content()

            if TARGET_KEYWORD in content:
                print(f"[FOUND] {TARGET_KEYWORD} detected at: {url}")
                found_urls.append(url)
            else:
                print(f"[NOT FOUND] {TARGET_KEYWORD} not present at: {url}")

            page.close()

        except Exception as e:
            print(f"[EXCEPTION] Could not fetch {url}: {e}")

    browser.close()

if found_urls:
    send_email(found_urls)
