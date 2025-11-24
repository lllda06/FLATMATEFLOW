import json
import redis

from django.core.mail import send_mail
from django.conf import settings

from .models import Notification

redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0)


def send_realtime_notification(user_id: int, event: str, payload: dict | None = None):
    """
    Отправка real-time уведомления через Redis в FastAPI.
    user_id — кому шлём (request.user.id или assigned_to.id)
    event — тип события, например: "invitation_created", "task_created", "task_completed"
    payload — любые данные, которые нужны на фронте
    """
    data = {
        "user_id": user_id,
        "event": event,
        "payload": payload or {},
    }
    try:
        redis_client.publish("notifications", json.dumps(data))
    except redis.exceptions.ConnectionError:
        # можно залогировать, но не падать
        pass


def create_notification(
    *,
    recipient,
    title: str,
    body: str,
    type: str = "generic",
    send_email: bool = False,
    email_subject: str | None = None,
    email_body: str | None = None,
    send_realtime: bool = True,
):
    ...
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        type=type,
    )

    if send_realtime:
        send_realtime_notification(
            user_id=recipient.id,
            event="notification_created",
            payload={
                "title": title,
                "body": body,
                "type": type,
            },
        )

    # Только если явно сказано send_email=True и у recipient есть email
    if send_email and recipient.email:
        subj = email_subject or title
        msg = email_body or body

        # Отправка письма
        send_mail(
            subject=subj,
            message=msg,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient.email],
            fail_silently=False,
        )

    return notification