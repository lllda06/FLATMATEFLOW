from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView
)

from accounts.api_jwt import MyTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),

    # твои приложения
    path("", include(("tasks.urls", "tasks"), namespace="tasks")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("api/", include("tasks.api.urls")),
    path('notifications/', include('notifications.urls')),


    # JWT
    path("api/auth/jwt/create/",  MyTokenObtainPairView.as_view(), name="jwt_create"),
    path("api/auth/jwt/refresh/", TokenRefreshView.as_view(),   name="jwt_refresh"),
    path("api/auth/jwt/verify/",  TokenVerifyView.as_view(),    name="jwt_verify"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)