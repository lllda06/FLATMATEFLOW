from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_INVITATION = "invitation_received"
    TYPE_TASK_ASSIGNED = "task_assigned"
    TYPE_TASK_COMPLETED = "task_completed"
    TYPE_SYSTEM = "system"

    TYPE_CHOICES = [
        (TYPE_INVITATION, "Приглашение в хозяйство"),
        (TYPE_TASK_ASSIGNED, "Новая задача"),
        (TYPE_TASK_COMPLETED, "Выполненная задача"),
        (TYPE_SYSTEM, "Системное уведомление"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=TYPE_SYSTEM,
    )
    body = models.TextField(blank=True, default="")
    payload = models.JSONField(blank=True, default=dict)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} – {self.body[:40]}"