import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Household(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    gift = models.CharField(max_length=150, verbose_name="Подарок победителю месяца")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_households",
        verbose_name="Создатель",
    )
    members = models.ManyToManyField(
        User,
        related_name="households",
        verbose_name="Участники",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Хозяйство"
        verbose_name_plural = "Хозяйства"

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Хозяйство",
    )
    title = models.CharField(max_length=200, verbose_name="Задача")
    description = models.TextField(blank=True, verbose_name="Описание")
    points = models.PositiveIntegerField(default=10, verbose_name="Баллы")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Назначено",
    )
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_tasks",
        verbose_name="Кем выполнено",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    completed_at = models.DateTimeField(
        null=True, blank=True, db_index=True, verbose_name="Выполнено в"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["household", "is_completed"]),
            models.Index(fields=["completed_at"]),
        ]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self) -> str:
        return f"{self.title} ({self.points} баллов)"


# --- helpers для значений по умолчанию (чтобы миграции собирались) ---

def invite_generate_token() -> str:
    return str(uuid.uuid4())


def invite_default_expires_at():
    return timezone.now() + timedelta(days=7)


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Ожидает"
        ACCEPTED = "ACCEPTED", "Принято"
        DECLINED = "DECLINED", "Отклонено"
        EXPIRED = "EXPIRED", "Просрочено"

    token = models.CharField(
        max_length=36, unique=True, default=invite_generate_token, editable=False
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name="Хозяйство",
    )
    inviter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
        verbose_name="Пригласивший",
    )
    # Если отправляем «по коду», invitee может быть пустым
    invitee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_invitations",
        verbose_name="Кого пригласили",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    expires_at = models.DateTimeField(
        default=invite_default_expires_at, verbose_name="Истекает"
    )
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Принято в")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["status", "expires_at"]),
        ]
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"

    def is_active(self) -> bool:
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()

    def __str__(self) -> str:
        who = self.invitee.username if self.invitee else "по коду"
        return f"Invite to {self.household.name} → {who} ({self.status})"
