import os
import requests

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

def send_slack(channel_label: str, text: str, blocks=None) -> bool:
    """
    Post to Slack via Incoming Webhook.
    `channel_label` is just a visual prefix; webhooks always post to the channel
    the webhook was created for.
    """
    if not SLACK_WEBHOOK:
        raise RuntimeError("SLACK_WEBHOOK not set")

    payload = {"text": f"[{channel_label}] {text}"}
    if blocks:
        payload["blocks"] = blocks  # Block Kit payload

    r = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
    if not r.ok:
        # surface Slack's response in NotificationLog.error
        raise RuntimeError(f"Slack webhook error {r.status_code}: {r.text}")
    return True


# Keep your email stub/implementation as-is
def send_email(recipients, subject, body):
    print("EMAIL:", recipients, subject, body)


