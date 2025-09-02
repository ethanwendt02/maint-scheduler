import os
import requests
from typing import List

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")  # set this in your env


def send_slack(channel: str, text: str):
    """
    Minimal Slack webhook sender. If SLACK_WEBHOOK is unset, no-op.
    """
    if not SLACK_WEBHOOK:
        return
    # Basic message; extend with blocks as needed.
    requests.post(SLACK_WEBHOOK, json={"text": f"[{channel}] {text}"})


def send_email(recipients: List[str], subject: str, body: str):
    """
    Stub email sender. Replace with SES/SendGrid later.
    """
    # For now, just print to console so you can see it's being called.
    print("EMAIL:", recipients, subject, body)
