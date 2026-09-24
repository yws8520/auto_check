import os
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from playwright.sync_api import sync_playwright

# List of target keywords to search for
TARGET_KEYWORDS = ["BX-52", "BX-53"]

# "https://www.toysrus.com.hk/zh-hk/search/?q=%28%E7%B6%B2%E5%BA%97%E9%A0%90%E8%B3%BC%29+Beyblade+X&lang=zh_HK&cgid=",

URLS = [
    "https://www.hobbylandeshop.com/product-category/nproduct_booking",
    "https://www.hobbylandeshop.com/product-category/takaratomy/beyblade%E9%99%80%E8%9E%BA",
    "https://fooklemodel.com/product-tag/pre-order/?_stockstatus=1",
    "https://lastchancetoy.com/search?q=BeybladeX",
]

# Credentials
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAILS = ["yws1024@gmail.com"]

TELEGRAM_GROUP_API_KEY = os.environ.get("TELEGRAM_GROUP_API_KEY")


def send_telegram_group_alert(matched_results):
    if not TELEGRAM_GROUP_API_KEY:
        print("[TELEGRAM ERROR] TELEGRAM_GROUP_API_KEY secret missing.")
        return

    # Construct formatted message for Telegram
    text_lines = ["🎯 Beyblade Stock Alert!", ""]
    for url, keywords in matched_results.items():
        kw_str = ", ".join(keywords)
        text_lines.append(f"• Keywords: {kw_str}")
        text_lines.append(f"  {url}\n")

    full_message = "\n".join(text_lines)

    # CallMeBot Telegram Group API Endpoint
    encoded_msg = urllib.parse.quote(full_message)
    api_url = f"https://api.callmebot.com/telegram/group.php?apikey={TELEGRAM_GROUP_API_KEY}&text={encoded_msg}"

    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            print("[TELEGRAM SUCCESS] Alert sent to Telegram group.")
        else:
            print(
                f"[TELEGRAM ERROR] Failed: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] Failed to send Telegram message: {e}")


def send_email(matched_results):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[EMAIL ERROR] SENDER_EMAIL or SENDER_PASSWORD secret missing.")
        return

    details_str = ""
    for url, keywords in matched_results.items():
        found_kw_str = ", ".join(keywords)
        details_str += f"• Page: {url}\n  Matched Keyword(s): {found_kw_str}\n\n"

    subject = "🎯 Stock Alert: Target Keyword Detected!"
    body = f"The following target keyword(s) were detected:\n\n{details_str}"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg, to_addrs=RECEIVER_EMAILS)
        print(
            f"[EMAIL SUCCESS] Alert email sent to {', '.join(RECEIVER_EMAILS)}"
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")


# Dictionary to store results: { url: [found_keyword_1, found_keyword_2] }
matched_results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for url in URLS:
        try:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            content = page.content()

            # Check which keywords are present on the page
            found_on_page = [kw for kw in TARGET_KEYWORDS if kw in content]

            if found_on_page:
                print(f"[FOUND] Keywords {found_on_page} detected at: {url}")
                matched_results[url] = found_on_page
            else:
                print(f"[NOT FOUND] Target keywords not present at: {url}")

            page.close()

        except Exception as e:
            print(f"[EXCEPTION] Could not fetch {url}: {e}")

    browser.close()

# Send Alerts if any keyword was found
if matched_results:
    send_telegram_group_alert(matched_results)
    send_email(matched_results)
