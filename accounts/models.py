from django.contrib.auth.models import AbstractUser
from django.db import models

def avatar_upload_path(instance, filename):
    return f"avatars/user_{instance.id}/{filename}"

class User(AbstractUser):
    # уже есть username, first_name, last_name, email и т.д.
    display_name = models.CharField("Отображаемое имя", max_length=50, blank=True)
    avatar = models.ImageField("Аватар", upload_to=avatar_upload_path, blank=True, null=True)

    # Настройки писем (на будущее, пригодятся для уведомлений)
    email_new_task = models.BooleanField("Письмо о новых задачах", default=True)
    email_invitation = models.BooleanField("Письмо о приглашениях", default=True)
    email_household_digest = models.BooleanField("Ежедневная сводка", default=False)
    email_household_invites = models.BooleanField(default=True, verbose_name="Получать письма о приглашениях в хозяйство",)

    def public_name(self):
        return self.display_name or self.get_full_name() or self.username

    def __str__(self):
        return self.public_name()