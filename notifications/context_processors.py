from .models import Notification

def notifications_counts(request):
    if request.user.is_authenticated:
        return {
            "unread_notifications_count": Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count()
        }
    return {}