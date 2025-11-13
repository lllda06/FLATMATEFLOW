from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Почта уже используется.")
        return email

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("display_name", "email", "first_name", "last_name")
        labels = {
            "display_name": "Отображаемое имя",
            "email": "E-mail",
            "first_name": "Имя",
            "last_name": "Фамилия",
        }

class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar",)
        labels = {"avatar": "Аватар"}

    def clean_avatar(self):
        f = self.cleaned_data.get("avatar")
        if not f:
            return f
        if f.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 2 МБ.")
        if not f.content_type.startswith("image/"):
            raise forms.ValidationError("Загрузите изображение (jpg/png/webp).")
        return f

class EmailPrefsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email_new_task", "email_invitation", "email_household_digest")
        labels = {
            "email_new_task": "Письма о новых заданиях",
            "email_invitation": "Письма о приглашениях",
            "email_household_digest": "Ежедневная сводка по баллам",
        }
