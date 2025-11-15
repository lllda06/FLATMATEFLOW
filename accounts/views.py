from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .forms import SignupForm, ProfileForm, AvatarForm, EmailPrefsForm

User = get_user_model()


def send_activation_email(request, user: User):
    """
    Отправка письма с ссылкой активации после регистрации.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_url = request.build_absolute_uri(
        reverse("accounts:activate", kwargs={"uidb64": uidb64, "token": token})
    )

    subject = "Подтверждение регистрации — FlatmateFlow"
    message = (
        f"Привет, {user.get_full_name() or user.username}!\n\n"
        f"Чтобы подтвердить адрес электронной почты и активировать аккаунт, "
        f"перейдите по ссылке:\n{activation_url}\n\n"
        f"Если вы не регистрировались в FlatmateFlow, просто проигнорируйте это письмо."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


class SignUpView(FormView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    # после регистрации ведём на логин, чтобы пользователь залогинился ПОСЛЕ подтверждения почты
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("tasks:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # создаём пользователя, но пока не активируем
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # отправляем письмо с подтверждением
        if user.email:
            try:
                send_activation_email(self.request, user)
                messages.info(
                    self.request,
                    "Мы отправили письмо с подтверждением на вашу почту. "
                    "Перейдите по ссылке в письме, чтобы активировать аккаунт.",
                )
            except Exception:
                # если с почтой что-то пошло не так — просто предупредим
                messages.error(
                    self.request,
                    "Не удалось отправить письмо с подтверждением. "
                    "Попробуйте позже или обратитесь к администратору.",
                )
        else:
            messages.warning(
                self.request,
                "У аккаунта не указан e-mail, подтверждение по почте невозможно.",
            )

        # НИКАКОГО автологина здесь больше нет
        return super().form_valid(form)


def activate(request, uidb64, token):
    """
    Активирует аккаунт по ссылке из письма.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        # если у тебя в моделе есть флаг email-подтверждения — тоже проставим
        if hasattr(user, "is_email_verified"):
            user.is_email_verified = True
        user.save()

        messages.success(request, "E-mail подтверждён, теперь вы можете войти.")
        return redirect("accounts:login")
    else:
        messages.error(
            request,
            "Ссылка активации недействительна или устарела. "
            "Попробуйте зарегистрироваться снова.",
        )
        return redirect("accounts:login")


@login_required
def profile(request):
    user = request.user

    if request.method == "POST":
        # Поймём, какую форму отправили (по имени кнопки)
        if "save_profile" in request.POST:
            pform = ProfileForm(request.POST, instance=user, prefix="p")
            aform = AvatarForm(instance=user, prefix="a")
            eform = EmailPrefsForm(instance=user, prefix="e")
            if pform.is_valid():
                pform.save()
                messages.success(request, "Профиль обновлён.")
                return redirect("accounts:profile")

        elif "save_avatar" in request.POST:
            pform = ProfileForm(instance=user, prefix="p")
            aform = AvatarForm(request.POST, request.FILES, instance=user, prefix="a")
            eform = EmailPrefsForm(instance=user, prefix="e")
            if aform.is_valid():
                aform.save()
                messages.success(request, "Аватар обновлён.")
                return redirect("accounts:profile")

        elif "save_prefs" in request.POST:
            pform = ProfileForm(instance=user, prefix="p")
            aform = AvatarForm(instance=user, prefix="a")
            eform = EmailPrefsForm(request.POST, instance=user, prefix="e")
            if eform.is_valid():
                eform.save()
                messages.success(request, "Настройки уведомлений сохранены.")
                return redirect("accounts:profile")
    else:
        pform = ProfileForm(instance=user, prefix="p")
        aform = AvatarForm(instance=user, prefix="a")
        eform = EmailPrefsForm(instance=user, prefix="e")

    return render(
        request,
        "accounts/profile.html",
        {"pform": pform, "aform": aform, "eform": eform},
    )