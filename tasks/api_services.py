# tasks/api_services.py
from django.db.models import Sum
from django.http import JsonResponse
from tasks.models import Household, Task
from django.shortcuts import get_object_or_404

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