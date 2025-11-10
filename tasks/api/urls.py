from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseholdViewSet, TaskViewSet, InvitationViewSet

router = DefaultRouter()
router.register(r'households', HouseholdViewSet, basename='api-households')
router.register(r'tasks', TaskViewSet, basename='api-tasks')
router.register(r'invitations', InvitationViewSet, basename='api-invitations')

urlpatterns = [
    path('', include(router.urls)),
]