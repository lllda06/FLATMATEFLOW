from .models import Notification


def create_notification(*, user, type, body="", payload=None):
    if payload is None:
        payload = {}

    return Notification.objects.create(
        user=user,
        type=type,
        body=body,
        payload=payload,
    )