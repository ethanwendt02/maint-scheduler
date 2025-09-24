# apps/notifications/slack.py
import os
from typing import Optional, Iterable, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "")

_client = WebClient(token=SLACK_BOT_TOKEN)

def _is_id(label: str) -> bool:
    return label and label[0] in ("C", "G")

def _normalize_name(label: str) -> str:
    label = (label or "").strip()
    return label[1:] if label.startswith("#") else label

def _resolve_channel_id(name: str) -> str:
    """
    Turn 'maintenance-scheduler' into a channel ID.
    Needs channels:read + groups:read. Raises with a clear message otherwise.
    """
    cursor = None
    while True:
        resp = _client.conversations_list(
            limit=1000,
            cursor=cursor,
            types="public_channel,private_channel",
        )
        for ch in resp.get("channels", []):
            if ch.get("name") == name:
                return ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    raise RuntimeError(
        f"Slack channel '#{name}' not found. "
        f"Make sure the bot has channels:read & groups:read, and the channel exists."
    )

def _ensure_in_channel(channel_id: str) -> None:
    try:
        _client.conversations_join(channel=channel_id)
    except SlackApiError as e:
        # ok if already in channel or joining not allowed (e.g., private)
        if e.response.get("error") not in ("already_in_channel", "method_not_supported_for_channel_type"):
            pass

def post_message(
    text: str,
    channel: Optional[str] = None,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
) -> dict:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN not set")

    label = (channel or SLACK_DEFAULT_CHANNEL)
    if not label:
        raise RuntimeError("No Slack channel provided and SLACK_DEFAULT_CHANNEL not set")

    # Accept #name, name, or ID
    if _is_id(label):
        channel_id = label
    else:
        channel_id = _resolve_channel_id(_normalize_name(label))

    _ensure_in_channel(channel_id)
    try:
        resp = _client.chat_postMessage(
            channel=channel_id, text=text or " ", blocks=blocks, thread_ts=thread_ts
        )
        return resp.data
    except SlackApiError as e:
        raise RuntimeError(f"Slack chat_postMessage failed: {e.response.get('error')}")

def upload_files(
    filepaths: Iterable[str],
    channel: Optional[str] = None,
    initial_comment: str = "",
    thread_ts: Optional[str] = None,
) -> List[dict]:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN not set")

    label = (channel or SLACK_DEFAULT_CHANNEL)
    if not label:
        raise RuntimeError("No Slack channel provided and SLACK_DEFAULT_CHANNEL not set")

    channel_id = label if _is_id(label) else _resolve_channel_id(_normalize_name(label))
    _ensure_in_channel(channel_id)

    results: List[dict] = []
    for fp in filepaths:
        try:
            resp = _client.files_upload_v2(
                channel=channel_id,
                initial_comment=initial_comment,
                file=fp,
                thread_ts=thread_ts,
            )
            results.append(resp.data)
        except SlackApiError as e:
            raise RuntimeError(f"Slack files_upload_v2 failed for {fp}: {e.response.get('error')}")
    return results

def send_slack(channel: Optional[str] = None,
               text: str = "",
               *,
               blocks: Optional[List[dict]] = None,
               thread_ts: Optional[str] = None) -> dict:
    return post_message(text=text, channel=channel, blocks=blocks, thread_ts=thread_ts)

