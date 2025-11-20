from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from notifications.models import Notification


def create_task(house, user, form):
    """
    Логика для создания задачи.
    """
    task = form.save(commit=False)
    task.household = house
    task.created_by = user
    task.save()

    # Создание уведомления для создателя задачи
    if user:  # Проверьте, что user не None
        notification = Notification.objects.create(
            recipient=user,  # убедитесь, что recipient назначен корректно
            title="Задача добавлена",
            body=f"Вы добавили задачу: {task.title}",
            type="info"
        )

        # Отправка уведомления по почте
        send_mail(
            subject="Задача добавлена",
            message=f"Задача: {task.title} была добавлена в ваше хозяйство.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],  # Отправляем уведомление на email создателя задачи
            fail_silently=False,
        )

    return task


def update_task_status(request, task, user):
    """
    Логика для изменения статуса задачи.
    """
    if task.is_completed:
        task.is_completed = False
        task.completed_by = None
        task.completed_at = None
        messages.info(request, "Задача снова отмечена как невыполненная.")
    else:
        task.is_completed = True
        task.completed_by = user
        task.completed_at = timezone.now()
        messages.success(request, f"Задача выполнена, начислено {task.points} баллов!")

        # Создаем уведомление, если задача выполнена
        notification = Notification.objects.create(
            recipient=task.created_by,  # Уведомление идет создателю задачи
            title="Задача выполнена",
            body=f"Задача {task.title} была выполнена. Вы получили {task.points} баллов.",
            type="info"
        )

        # Отправка уведомления по почте
        send_mail(
            subject="Задача выполнена",
            message=f"Задача: {task.title} была выполнена. Вы получили {task.points} баллов.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.created_by.email],  # Отправляем уведомление на email создателя задачи
            fail_silently=False,
        )

    task.save()
    return task