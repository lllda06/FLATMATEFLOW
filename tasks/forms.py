from django import forms
from .models import Household, Task
from django.contrib.auth.models import User

class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ["name", "description", "gift"]

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "points", "assigned_to"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3})
        }

class InviteByUsernameForm(forms.Form):
    username = forms.CharField(label="Логин пользователя", max_length=150)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь с таким логином не найден.")