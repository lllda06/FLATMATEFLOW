from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Invitation, Task
from notifications.utils import create_notification


@receiver(post_save, sender=Invitation)
def on_invitation_created(sender, instance, created, **kwargs):
    """
    Когда создаётся приглашение — отправляем уведомление приглашённому.
    """
    if not created:
        return

    invitee = instance.invitee
    if not invitee:
        return

    household = instance.household

    # Текст для in-app уведомления
    title = "Новое приглашение в хозяйство"
    body = f"Вас пригласили в хозяйство «{household.name}»."

    # Текст письма
    email_subject = "Приглашение в FlatmateFlow"
    email_body = (
        f"Привет, {invitee.get_full_name() or invitee.username}!\n\n"
        f"Пользователь {instance.inviter.get_full_name() or instance.inviter.username} "
        f"пригласил(а) вас в хозяйство «{household.name}».\n\n"
        f"Зайдите в раздел «Приглашения» на сайте FlatmateFlow, "
        f"чтобы принять или отклонить приглашение."
    )

    create_notification(
        recipient=invitee,
        type="invitation",
        title=title,
        body=body,
        send_email=getattr(invitee, "email_household_invites", False),
        email_subject=email_subject,
        email_body=email_body,
    )


@receiver(post_save, sender=Task)
def on_task_created(sender, instance, created, **kwargs):
    """
    Когда создаётся новая задача — шлём уведомления участникам хозяйства.
    """
    if not created:
        return

    task = instance
    household = task.household

    # Кого уведомляем: всех участников, кроме создателя
    members_qs = household.members.exclude(id=task.created_by_id)

    title = "Новая задача в хозяйстве"
    body_template = (
        f"В хозяйстве «{household.name}» создана новая задача: «{task.title}»."
    )

    for member in members_qs:
        email_subject = "Новая задача в FlatmateFlow"
        email_body = (
            f"Привет, {member.get_full_name() or member.username}!\n\n"
            f"В хозяйстве «{household.name}» появилась новая задача:\n"
            f"«{task.title}».\n\n"
            f"Зайдите в FlatmateFlow, чтобы посмотреть подробности и статус задачи."
        )

        create_notification(
            recipient=member,
            type="task_created",
            title=title,
            body=body_template,
            send_email=getattr(member, "email_task_updates", False),
            email_subject=email_subject,
            email_body=email_body,
        )