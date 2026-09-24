import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from playwright.sync_api import sync_playwright

# List of target keywords to search for
TARGET_KEYWORDS = ["爆旋陀螺", "BX-52", "BX-53"]

# "https://www.toysrus.com.hk/zh-hk/search/?q=%28%E7%B6%B2%E5%BA%97%E9%A0%90%E8%B3%BC%29+Beyblade+X&lang=zh_HK&cgid=",
URLS = [
    "https://www.hobbylandeshop.com/product-category/nproduct_booking",
]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAILS = ["yws1024@gmail.com", "yws212@ha.org.hk"]

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GITHUB_WORKFLOW_ID = os.environ.get("GITHUB_WORKFLOW_ID")


def send_email(matched_results):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[EMAIL ERROR] SENDER_EMAIL or SENDER_PASSWORD secret missing.")
        return

    # Build clear details for matched keywords and links
    details_str = ""
    for url, keywords in matched_results.items():
        found_kw_str = ", ".join(keywords)
        details_str += f"• Page: {url}\n  Matched Keyword(s): {found_kw_str}\n\n"

    subject = f"🎯 Stock Alert: Target Keyword Detected!"
    body = (
        f"The following target keyword(s) were detected:\n\n"
        f"{details_str}"
        f"The workflow has been automatically disabled to stop further emails."
    )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg, to_addrs=RECEIVER_EMAILS)
        print(f"[EMAIL SUCCESS] Alert email sent to {', '.join(RECEIVER_EMAILS)}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")


def disable_github_workflow():
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY or not GITHUB_WORKFLOW_ID:
        print("[GITHUB API ERROR] Missing GitHub environment tokens.")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/{GITHUB_WORKFLOW_ID}/disable"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        print(f"[GITHUB API SUCCESS] Workflow '{GITHUB_WORKFLOW_ID}' successfully disabled.")
    else:
        print(f"[GITHUB API ERROR] Failed to disable workflow: {response.status_code} - {response.text}")


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
                print(f"[NOT FOUND] No target keywords present at: {url}")

            page.close()

        except Exception as e:
            print(f"[EXCEPTION] Could not fetch {url}: {e}")

    browser.close()

# Send Email AND disable workflow if any keyword was found
if matched_results:
    send_email(matched_results)
    disable_github_workflow()
