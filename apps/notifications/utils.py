# apps/notifications/utils.py
from typing import Optional, List, Iterable
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# Use the canonical Slack sender
from .slack import send_slack as _send_slack


def send_slack(
    channel_label: Optional[str],
    text: str,
    *,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
) -> bool:
    """
    Legacy wrapper so old imports keep working.
    """
    _send_slack(channel=channel_label, text=text, blocks=blocks, thread_ts=thread_ts)
    return True


def send_email(
    to: Iterable[str] | str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
) -> bool:
    """
    Simple email helper used by legacy code paths.
    Uses Django's EmailMultiAlternatives.
    """
    if isinstance(to, str):
        to = [to]

    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@localhost"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=from_email,
        to=list(to),
    )
    if html_body:
        msg.attach_alternative(html_body, "text/html")
    msg.send()  # will raise if email backend is misconfigured
    return True

