from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Household, Task, Invitation

User = get_user_model()


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ["name", "description", "gift"]


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "points", "assigned_to"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class InviteByUsernameForm(forms.Form):
    username = forms.CharField(label="Логин пользователя", max_length=150)

    def __init__(self, *args, household=None, inviter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.household = household
        self.inviter = inviter

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        # берём пользователя из кастомной модели
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь с таким логином не найден.")

        if self.inviter and user == self.inviter:
            raise forms.ValidationError("Нельзя отправить приглашение самому себе.")

        if self.household and self.household.members.filter(pk=user.pk).exists():
            raise forms.ValidationError("Этот пользователь уже состоит в хозяйстве.")

        self.cleaned_data["user"] = user
        return user  # возвращаем сам объект User — в вьюхе это подойдёт для invitee

    def save(self):
        """Удобный helper, чтобы сразу создать приглашение."""
        invitee = self.cleaned_data["user"]
        return Invitation.objects.create(
            household=self.household,
            inviter=self.inviter,
            invitee=invitee,
            created_at=timezone.now(),
        )