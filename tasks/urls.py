from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.home, name="home"),
    path("households/", views.dashboard, name="dashboard"),
    path("households/create/", views.household_create, name="household_create"),
    path("households/<int:pk>/", views.household_detail, name="household_detail"),
    path("households/<int:pk>/stats/", views.household_stats, name="household_stats"),

    path("households/<int:pk>/tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:task_id>/toggle/", views.task_toggle_done, name="task_toggle_done"),

    # приглашения
    path("households/<int:pk>/invite/username/", views.invite_by_username, name="invite_by_username"),
    path("households/<int:pk>/invite/code/", views.invite_generate_code, name="invite_generate_code"),
    path("invite/accept/<str:token>/", views.invite_accept_token, name="invite_accept_token"),
    path("invite/inbox/", views.invitations_inbox, name="invitations_inbox"),
    path("invite/<int:inv_id>/decline/", views.invite_decline, name="invite_decline"),

    # auth
    path("signup/", views.signup, name="signup"),

    # простые API
    path("api/households/", views.api_households, name="api_households"),
    path("api/households/<int:pk>/tasks/", views.api_household_tasks, name="api_household_tasks"),
    path("api/households/<int:pk>/stats/", views.api_household_stats, name="api_household_stats"),
]
