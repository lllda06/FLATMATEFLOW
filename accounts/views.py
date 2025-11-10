from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import SignupForm

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
