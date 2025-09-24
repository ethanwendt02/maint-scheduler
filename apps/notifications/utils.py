# apps/notifications/utils.py
from typing import Optional, List, Iterable
from .slack import send_slack as _send_slack, post_message as _post_message
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def send_slack(channel_label: Optional[str], text: str, *, blocks: Optional[List[dict]] = None) -> bool:
    _send_slack(channel=channel_label, text=text, blocks=blocks)
    return True

def send_email(to: Iterable[str] | str, subject: str, body: str, html_body: Optional[str] = None, from_email: Optional[str] = None) -> bool:
    if isinstance(to, str):
        to = [to]
    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")
    msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=list(to))
    if html_body:
        msg.attach_alternative(html_body, "text/html")
    msg.send()
    return True


