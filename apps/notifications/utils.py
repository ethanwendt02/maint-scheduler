# apps/notifications/utils.py
from __future__ import annotations

from typing import List, Optional, Dict, Any

from .slack import post_message, upload_files


def send_slack(
    channel: Optional[str],
    text: str,
    blocks: Optional[list] = None,
    files: Optional[List[str]] = None,
    initial_comment: str = "Attachments",
) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper used across the project.

    Uses Slack Web API (bot token) via apps/notifications/slack.py
    instead of legacy incoming webhook posts.

    - channel: can be None (slack.py will fall back to env default)
    - blocks: optional Block Kit
    - files: optional list of file paths to upload (will thread under message)
    """
    resp = post_message(text=text, channel=channel, blocks=blocks)

    # If a message posted successfully, you can thread file uploads under it
    thread_ts = resp.get("ts")
    if files:
        upload_files(
            filepaths=files,
            channel=channel,
            initial_comment=initial_comment,
            thread_ts=thread_ts,
        )

    return resp


def send_email(recipients: List[str], subject: str, body: str) -> None:
    # Keep this stub (or wire SES/SendGrid later).
    # The point is: don't break existing imports.
    print("EMAIL:", recipients, subject, body)
