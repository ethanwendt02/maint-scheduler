# apps/notifications/utils.py
from typing import Optional, List
from .slack import send_slack as _send_slack  # canonical implementation

def send_slack(
    channel_label: Optional[str],
    text: str,
    *,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
) -> bool:
    """
    Legacy wrapper so old imports keep working.
    `channel_label` can be a Slack channel ID (C.../G...) or a channel name.
    """
    _send_slack(channel=channel_label, text=text, blocks=blocks, thread_ts=thread_ts)
    return True

