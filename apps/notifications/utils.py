import os
import requests
from typing import List, Optional, Dict, Any

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

def _post_to_slack(payload: Dict[str, Any]) -> None:
    """
    Low-level poster. No-ops if SLACK_WEBHOOK isn't set.
    """
    if not SLACK_WEBHOOK:
        return
    # Slack Incoming Webhooks expect JSON as the full message body.
    requests.post(SLACK_WEBHOOK, json=payload, timeout=10)

def send_slack(
    channel: Optional[str],
    text: str,
    blocks: Optional[list] = None,
) -> None:
    """
    High-level helper. 
    - If `blocks` is provided, Slack shows rich layout.
    - `channel` is optional; if your webhook allows overriding, pass "#maintenance-scheduler".
    """
    payload: Dict[str, Any] = {"text": text}
    if channel:
        payload["channel"] = channel  # works only if the webhook integration allows channel override
    if blocks:
        payload["blocks"] = blocks
    _post_to_slack(payload)

def send_email(recipients: List[str], subject: str, body: str) -> None:
    # stub: integrate SES/SendGrid; for dev just print
    print("EMAIL:", recipients, subject, body)



