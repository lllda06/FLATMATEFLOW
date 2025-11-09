from calendar import monthrange

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden, Http404, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from django.urls import reverse

from .models import Household, Task, Invitation
from .forms import HouseholdForm, TaskForm, InviteByUsernameForm

def home(request):
    return render(request, "tasks/home.html")

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан, добро пожаловать!")
            return redirect("tasks:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "auth/signup.html", {"form": form})

@login_required
def dashboard(request):
    # Хозяйства, где пользователь участник или создатель
    households = Household.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
    return render(request, "tasks/dashboard.html", {"households": households})

@login_required
def household_create(request):
    if request.method == "POST":
        form = HouseholdForm(request.POST)
        if form.is_valid():
            house = form.save(commit=False)
            house.created_by = request.user
            house.save()
            house.members.add(request.user)  # автор сразу участник
            messages.success(request, "Хозяйство создано.")
            return redirect("tasks:household_detail", pk=house.pk)
    else:
        form = HouseholdForm()
    return render(request, "tasks/household_create.html", {"form": form})

@login_required
def household_detail(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа к этому хозяйству.")

    tasks = house.tasks.order_by("-created_at")
    task_form = TaskForm()
    return render(request, "tasks/household_detail.html", {"house": house, "tasks": tasks, "task_form": task_form})

@login_required
def task_create(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.household = house
            task.save()
            messages.success(request, "Задача добавлена.")
    return redirect("tasks:household_detail", pk=pk)

@login_required
def task_toggle_done(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    house = task.household
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    if task.is_completed:
        # Снять выполнение
        task.is_completed = False
        task.completed_by = None
        task.completed_at = None
        messages.info(request, "Задача снова отмечена как невыполненная.")
    else:
        # Отметить выполненной
        task.is_completed = True
        task.completed_by = request.user
        task.completed_at = timezone.now()
        messages.success(request, f"Задача выполнена, начислено {task.points} баллов!")
    task.save()
    return redirect("tasks:household_detail", pk=house.pk)

@login_required
def household_stats(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")

    # Текущий месяц
    now = timezone.localtime()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = monthrange(now.year, now.month)[1]
    end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    # Агрегация по выполненным задачам за месяц
    completed = Task.objects.filter(
        household=house,
        is_completed=True,
        completed_at__range=(start, end),
        completed_by__isnull=False
    ).values("completed_by__username").annotate(total=Sum("points")).order_by("-total")

    total_points = completed.aggregate(Sum("total"))["total__sum"] or 0
    return render(
        request,
        "tasks/stats.html",
        {"house": house, "completed": completed, "total_points": total_points, "period": (start, end)}
    )

# -------- REST (простые JSON) --------
@login_required
def api_households(request):
    qs = Household.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
    data = [{"id": h.id, "name": h.name, "gift": h.gift, "members": [m.username for m in h.members.all()]} for h in qs]
    return JsonResponse(data, safe=False)

@login_required
def api_household_tasks(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return JsonResponse({"detail": "forbidden"}, status=403)
    tasks = house.tasks.order_by("-created_at")
    data = [{
        "id": t.id, "title": t.title, "points": t.points, "assigned_to": t.assigned_to.username if t.assigned_to else None,
        "is_completed": t.is_completed, "completed_by": t.completed_by.username if t.completed_by else None
    } for t in tasks]
    return JsonResponse(data, safe=False)

@login_required
def api_household_stats(request, pk):
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return JsonResponse({"detail": "forbidden"}, status=403)
    now = timezone.localtime()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = monthrange(now.year, now.month)[1]
    end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    completed = Task.objects.filter(household=house, is_completed=True, completed_at__range=(start, end),
                                    completed_by__isnull=False
                                    ).values("completed_by__username").annotate(total=Sum("points")).order_by("-total")
    return JsonResponse(list(completed), safe=False)

@login_required
def invitations_inbox(request):
    """Входящие приглашения текущего пользователя"""
    inbox = Invitation.objects.filter(invitee=request.user, status=Invitation.Status.PENDING, expires_at__gt=timezone.now())
    return render(request, "tasks/invitations_inbox.html", {"inbox": inbox})

@login_required
def invite_by_username(request, pk):
    """Пригласить конкретного пользователя по логину"""
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
            messages.success(request, f"Приглашение отправлено пользователю {user.username}.")
            return redirect("tasks:household_detail", pk=pk)
    else:
        form = InviteByUsernameForm()
    return render(request, "tasks/invite_by_username.html", {"house": house, "form": form})

@login_required
def invite_generate_code(request, pk):
    """Сгенерировать код/ссылку для присоединения (без конкретного адресата)"""
    house = get_object_or_404(Household, pk=pk)
    if request.user not in house.members.all() and request.user != house.created_by:
        return HttpResponseForbidden("Нет доступа.")
    inv = Invitation.objects.create(household=house, inviter=request.user)  # invitee=None → «по коду»
    link = request.build_absolute_uri(reverse("tasks:invite_accept_token", args=[inv.token]))
    messages.success(request, f"Ссылка приглашения создана: {link}")
    return redirect("tasks:household_detail", pk=pk)

@login_required
def invite_accept_token(request, token):
    """Принять приглашение по ссылке-коду"""
    inv = get_object_or_404(Invitation, token=token)
    if not inv.is_active():
        if inv.status == Invitation.Status.PENDING and inv.expires_at <= timezone.now():
            inv.status = Invitation.Status.EXPIRED
            inv.save(update_fields=["status"])
        messages.error(request, "Приглашение недействительно.")
        return redirect("tasks:dashboard")
    # Если приглашение адресное — только конкретный получатель может принять
    if inv.invitee and inv.invitee != request.user:
        messages.error(request, "Это приглашение адресовано другому пользователю.")
        return redirect("tasks:dashboard")

    inv.household.members.add(request.user)
    inv.status = Invitation.Status.ACCEPTED
    inv.accepted_at = timezone.now()
    inv.save(update_fields=["status", "accepted_at"])
    messages.success(request, f"Вы присоединились к «{inv.household.name}».")
    return redirect("tasks:household_detail", pk=inv.household.pk)

@login_required
def invite_decline(request, inv_id):
    """Отклонить адресное приглашение"""
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
