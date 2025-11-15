from django.core.mail import send_mail
from django.conf import settings

from .models import Notification


def create_notification(
    *,
    recipient,
    title: str,
    body: str,
    type: str = "generic",
    send_email: bool = False,
    email_subject: str | None = None,
    email_body: str | None = None,
):
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        type=type,
    )

    # Только если явно сказано send_email=True
    if send_email and getattr(recipient, "email", None):
        subj = email_subject or title
        msg = email_body or body

        send_mail(
            subject=subj,
            message=msg,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient.email],
            fail_silently=False,
        )

    return notification