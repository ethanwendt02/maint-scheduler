# apps/notifications/slack.py
import os
from typing import Optional, Iterable, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "")

_client = WebClient(token=SLACK_BOT_TOKEN)

def _looks_like_id(label: str) -> bool:
    return label and (label[0] in ("C", "G")) and label.isalnum()

def _resolve_channel_id(label: str) -> str:
    """
    Accepts 'C…/G…' IDs or '#name'/ 'name'.
    Requires channels:read and groups:read to resolve by name.
    """
    if not label:
        raise RuntimeError("No Slack channel provided")
    label = label.strip()
    if _looks_like_id(label):
        return label
    if label.startswith("#"):
        label = label[1:]

    # Try to find by name across public + private channels
    cursor = None
    while True:
        resp = _client.conversations_list(
            limit=1000,
            cursor=cursor,
            types="public_channel,private_channel",
        )
        for ch in resp["channels"]:
            if ch.get("name") == label:
                return ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    raise RuntimeError(
        f"Slack channel '{label}' not found. Use a channel ID or grant channels:read, groups:read."
    )

def _ensure_join_if_public(channel_id: str) -> None:
    """
    Best-effort join for public channels so the bot can post.
    Private channels still require a manual invite.
    """
    try:
        _client.conversations_join(channel=channel_id)
    except SlackApiError as e:
        # not_in_channel for private channels or already_in_channel -> ignore
        if e.response.get("error") not in ("already_in_channel", "method_not_supported_for_channel_type"):
            # For private channels, joining isn't allowed; they'll need to invite the bot.
            pass

def post_message(
    text: str,
    channel: Optional[str] = None,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
) -> dict:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN not set")
    channel_label = channel or SLACK_DEFAULT_CHANNEL
    if not channel_label:
        raise RuntimeError("No Slack channel provided and SLACK_DEFAULT_CHANNEL not set")

    channel_id = _resolve_channel_id(channel_label)
    _ensure_join_if_public(channel_id)

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
    channel_label = channel or SLACK_DEFAULT_CHANNEL
    channel_id = _resolve_channel_id(channel_label)
    _ensure_join_if_public(channel_id)

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


