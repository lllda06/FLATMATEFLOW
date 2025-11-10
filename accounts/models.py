from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    display_name = models.CharField('Отображаемое имя', max_length=150, blank=True)
    avatar = models.URLField('Аватар (URL)', blank=True)

    def __str__(self):
        return self.display_name or self.get_full_name() or self.username
