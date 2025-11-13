from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invitation
from notifications.utils import create_notification
from notifications.models import Notification


@receiver(post_save, sender=Invitation)
def on_invitation_created(sender, instance, created, **kwargs):
    if not created:
        return

    invited_user = instance.invitee  # уже поправили

    # создаём уведомление БЕЗ title
    create_notification(
        user=invited_user,
        type=Notification.TYPE_INVITATION,
        body=f"Вас пригласили в хозяйство «{instance.household.name}» от пользователя {instance.inviter.username}.",
        payload={
            "household_id": instance.household_id,
            "invitation_id": instance.id,
            "inviter": instance.inviter.username,
        },
    )