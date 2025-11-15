from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Notification


@login_required
def notifications_list(request):
    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .order_by('-created_at')
    )
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
    })


@login_required
def mark_all_read(request):
    (
        Notification.objects
        .filter(recipient=request.user, is_read=False)
        .update(is_read=True, read_at=timezone.now())
    )
    # возвращаем туда, откуда пришли, либо на страницу уведомлений
    next_url = request.GET.get('next') or 'notifications:list'
    return redirect(next_url)