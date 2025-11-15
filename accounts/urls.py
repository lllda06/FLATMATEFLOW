from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView, activate
from . import views

app_name = 'accounts'

urlpatterns = [
    path(
        'login/', auth_views.LoginView.as_view(template_name='auth/login.html'),
        name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("signup/", SignUpView.as_view(), name="signup"),

    path("profile/", views.profile, name="profile"),

    path("password/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change.html",
        success_url="/accounts/password/done/",
    ), name="password_change"),
    path("password/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html",
    ), name="password_change_done"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
]
