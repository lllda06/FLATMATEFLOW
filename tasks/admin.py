from django.contrib import admin
from .models import Household, Task, Invitation


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "gift", "created_by", "created_at")
    search_fields = ("name", "gift")
    filter_horizontal = ("members",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "household", "points", "assigned_to", "is_completed", "completed_by", "completed_at")
    list_filter = ("household", "is_completed")
    search_fields = ("title", "description")

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("household", "inviter", "invitee", "status", "created_at", "expires_at")
    list_filter = ("status", "household")
    search_fields = ("token", "household__name", "inviter__username", "invitee__username")