import os
import requests
from typing import List, Optional

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

def send_slack(channel_label: str, text: str) -> bool:
    """
    Send a message to Slack via Incoming Webhook.
    `channel_label` is just a label prefix (e.g., '#ops') for clarity in the message.
    Returns True/False for success.
    """
    if not SLACK_WEBHOOK:
        return False
    resp = requests.post(
        SLACK_WEBHOOK,
        json={"text": f"[{channel_label}] {text}"},
        timeout=10,
    )
    return resp.ok

def send_email(recipients: List[str], subject: str, body: str):
    # stub: integrate SES/SendGrid; for dev just print
    print("EMAIL:", recipients, subject, body)

