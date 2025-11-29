from django.db.models import Sum
from django.http import JsonResponse

from notifications.models import Notification
from tasks.models import Household, Task
from django.shortcuts import get_object_or_404
from tasks.stats_service import get_stats_for_household

def get_households(request):
    """API для получения всех хозяйств текущего пользователя"""
    households = Household.objects.filter(members=request.user)
    data = [{"id": h.id, "name": h.name, "gift": h.gift} for h in households]
    return JsonResponse(data, safe=False)

def get_household_tasks(request, pk):
    """API для получения всех задач для конкретного хозяйства"""
    house = get_object_or_404(Household, pk=pk)
    tasks = house.tasks.all()
    data = [{
        "id": task.id,
        "title": task.title,
        "is_completed": task.is_completed,
        "assigned_to": task.assigned_to.username if task.assigned_to else None
    } for task in tasks]
    return JsonResponse(data, safe=False)

def get_household_stats(request, pk):
    """API для получения статистики по задачам для хозяйства"""
    house = get_object_or_404(Household, pk=pk)
    # Логика для статистики (например, количество выполненных задач)
    completed_tasks = house.tasks.filter(is_completed=True).count()
    total_points = house.tasks.filter(is_completed=True).aggregate(Sum('points'))['points__sum']
    return JsonResponse({
        'completed_tasks': completed_tasks,
        'total_points': total_points
    })

from tasks.stats_service import get_stats_for_household

def get_stats_for_household(request, pk):
    house = get_object_or_404(Household, pk=pk)
    stats = get_stats_for_household(house)

    return JsonResponse({
        "period_start": stats["period"][0],
        "period_end": stats["period"][1],
        "completed": stats["completed"],
        "total_points": stats["total_points"],
    })

# API для подсчета непрочитанных уведомлений
def unread_count(request):
    if request.user.is_authenticated:
        # Получаем количество непрочитанных уведомлений
        unread_notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return JsonResponse({"unread_count": unread_notifications})
    return JsonResponse({"error": "User not authenticated"}, status=401)