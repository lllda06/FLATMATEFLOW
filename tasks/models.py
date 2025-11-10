import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings


class Household(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    gift = models.CharField(max_length=150, help_text="Подарок победителю месяца")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_households"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="households"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Task(models.Model):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=10)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks"
    )
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_tasks"
    )
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.title} ({self.points} баллов)"


def invite_generate_token():
    return str(uuid.uuid4())

def invite_default_expires_at():
    return timezone.now() + timedelta(days=7)


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Ожидает"
        ACCEPTED = "ACCEPTED", "Принято"
        DECLINED = "DECLINED", "Отклонено"
        EXPIRED  = "EXPIRED",  "Просрочено"

    token = models.CharField(
        max_length=36,
        unique=True,
        default=invite_generate_token,
        editable=False
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="invitations"
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations"
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_invitations"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=invite_default_expires_at)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()

    def __str__(self):
        who = self.invitee.username if self.invitee else "по коду"
        return f"Invite to {self.household.name} → {who} ({self.status})"
