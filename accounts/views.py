from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render,redirect
from django.urls import reverse,reverse_lazy
from django.views.generic import FormView

from .forms import SignupForm, ProfileForm, AvatarForm, EmailPrefsForm

class SignUpView(FormView):
    template_name = "auth/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("tasks:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("tasks:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)          # автологин после регистрации
        return super().form_valid(form)

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