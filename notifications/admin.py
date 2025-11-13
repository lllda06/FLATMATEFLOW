# notifications/admin.py
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "body", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("body", "user__username", "user__email")