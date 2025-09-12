import os
from typing import Optional, Iterable
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "")

_client = WebClient(token=SLACK_BOT_TOKEN)

def post_message(
    text: str,
    channel: Optional[str] = None,
    blocks: Optional[list] = None,
    thread_ts: Optional[str] = None,
) -> dict:
    """
    Post a message to Slack. `channel` should be a channel ID (C… or G…).
    Returns Slack response (contains 'ts' for threading).
    """
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN not set")
    channel = channel or SLACK_DEFAULT_CHANNEL
    if not channel:
        raise RuntimeError("No Slack channel provided and SLACK_DEFAULT_CHANNEL not set")

    try:
        resp = _client.chat_postMessage(channel=channel, text=text or " ", blocks=blocks, thread_ts=thread_ts)
        return resp.data
    except SlackApiError as e:
        raise RuntimeError(f"Slack chat_postMessage failed: {e.response.get('error')}")
    

def upload_files(
    filepaths: Iterable[str],
    channel: Optional[str] = None,
    initial_comment: str = "",
    thread_ts: Optional[str] = None,
) -> list[dict]:
    """
    Upload one or more files to Slack. `filepaths` are absolute paths on disk.
    """
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN not set")
    channel = channel or SLACK_DEFAULT_CHANNEL
    if not channel:
        raise RuntimeError("No Slack channel provided and SLACK_DEFAULT_CHANNEL not set")

    results = []
    for fp in filepaths:
        try:
            resp = _client.files_upload_v2(
                channel=channel,
                initial_comment=initial_comment,
                file=fp,
                thread_ts=thread_ts,
            )
            results.append(resp.data)
        except SlackApiError as e:
            raise RuntimeError(f"Slack files_upload_v2 failed for {fp}: {e.response.get('error')}")
    return results
