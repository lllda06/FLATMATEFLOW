from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse

from tasks.api_services import get_households, get_household_tasks, get_household_stats
from tasks.forms import TaskForm, HouseholdForm, InviteByUsernameForm
from tasks.models import Household, Task, Invitation
from tasks.services import create_task, update_task_status
from notifications.utils import send_realtime_notification
from tasks.stats_service import get_stats_for_household


# Главная страница
def home(request):
    return render(request, 'tasks/home.html')


# Панель управления (dashboard) пользователя
@login_required
def dashboard(request):
    households = Household.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
    return render(request, "tasks/dashboard.html", {"households": households})


# Создание нового хозяйства
@login_required
def household_create(request):
    if request.method == "POST":
        form = HouseholdForm(request.POST)
        if form.is_valid():
            house = form.save(commit=False)
            house.created_by = request.user
            house.save()
            house.members.add(request.user)  # Автор сразу становится участником
            messages.success(request, "Хозяйство создано.")
            return redirect("tasks:household_detail", pk=house.pk)
    else:
        form = HouseholdForm()
    return render(request, "tasks/household_create.html", {"form": form})


# Детали хозяйства
@login_required
def household_detail(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа к этому хозяйству.")

    tasks = house.tasks.order_by("-created_at")
    task_form = TaskForm()
    return render(request, "tasks/household_detail.html", {"house": house, "tasks": tasks, "task_form": task_form})


# Создание задачи
@login_required
def task_create(request, pk):
    house = get_object_or_404(Household, pk=pk)

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = create_task(house, request.user, form)
            if task.assigned_to:
                send_realtime_notification(
                    user_id=task.assigned_to.id,
                    event="task_created",
                    payload={
                        "task_title": task.title,
                        "household": house.name,
                    },
                )
            messages.success(request, "Задача добавлена.")
            return redirect("tasks:household_detail", pk=pk)

    return render(request, "tasks/task_form.html", {"form": form, "house": house})


# Переключение статуса задачи (выполнена/не выполнена)
@login_required
def task_toggle_done(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    house = task.household
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    # Вызов функции с передачей request
    update_task_status(request, task, request.user)

    return redirect("tasks:household_detail", pk=house.pk)


# Статистика по хозяйству
@login_required
def household_stats(request, pk):
    house = get_object_or_404(Household, pk=pk)

    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    stats = get_stats_for_household(house)

    return render(request, "tasks/stats.html", {
        "house": house,
        "period": stats["period"],
        "completed": stats["completed"],
        "total_points": stats["total_points"],
    })


# Приглашение пользователя по логину
@login_required
def invite_by_username(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    if request.method == "POST":
        form = InviteByUsernameForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["username"]
            if user in house.members.all():
                messages.info(request, "Этот пользователь уже состоит в хозяйстве.")
                return redirect("tasks:household_detail", pk=pk)
            inv = Invitation.objects.create(household=house, inviter=request.user, invitee=user)
            send_realtime_notification(
                user_id=user.id,
                event="invitation_created",
                payload={
                    "household_name": house.name,
                    "inviter": request.user.username,
                },
            )
            messages.success(request, f"Приглашение отправлено пользователю {user.username}.")
            return redirect("tasks:household_detail", pk=pk)
    else:
        form = InviteByUsernameForm()
    return render(request, "tasks/invite_by_username.html", {"house": house, "form": form})


# Генерация кода приглашения
@login_required
def invite_generate_code(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    inv = Invitation.objects.create(household=house, inviter=request.user)  # invitee=None → «по коду»
    link = request.build_absolute_uri(reverse("tasks:invite_accept_token", args=[inv.token]))
    messages.success(request, f"Ссылка приглашения создана: {link}")
    return redirect("tasks:household_detail", pk=pk)


# Входящие приглашения
@login_required
def invitations_inbox(request):
    inbox = Invitation.objects.filter(invitee=request.user, status=Invitation.Status.PENDING,
                                      expires_at__gt=timezone.now())
    return render(request, "tasks/invitations_inbox.html", {"inbox": inbox})


# Принять приглашение по ссылке
@login_required
def invite_accept_token(request, token):
    inv = get_object_or_404(Invitation, token=token)
    if not inv.is_active():
        messages.error(request, "Приглашение недействительно.")
        return redirect("tasks:dashboard")

    inv.household.members.add(request.user)
    inv.status = Invitation.Status.ACCEPTED
    inv.accepted_at = timezone.now()
    inv.save(update_fields=["status", "accepted_at"])
    messages.success(request, f"Вы присоединились к «{inv.household.name}».")
    return redirect("tasks:household_detail", pk=inv.household.pk)


# Отклонить приглашение
@login_required
def invite_decline(request, inv_id):
    inv = get_object_or_404(Invitation, id=inv_id, invitee=request.user)
    if not inv.is_active():
        if inv.status == Invitation.Status.PENDING and inv.expires_at <= timezone.now():
            inv.status = Invitation.Status.EXPIRED
        else:
            inv.status = Invitation.Status.DECLINED
        inv.save(update_fields=["status"])
        return redirect("tasks:invitations_inbox")

    inv.status = Invitation.Status.DECLINED
    inv.save(update_fields=["status"])
    messages.info(request, "Приглашение отклонено.")
    return redirect("tasks:invitations_inbox")

# api_services

@login_required
def api_households(request):
    return get_households(request)

@login_required
def api_household_tasks(request, pk):
    return get_household_tasks(request, pk)

@login_required
def api_household_stats(request, pk):
    return get_household_stats(request, pk)