from django.db import models
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from tasks.models import Household, Task, Invitation
from .serializers import HouseholdSerializer, TaskSerializer, InvitationSerializer

class IsOwnerOrMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Household):
            return obj.created_by_id == request.user.id or obj.members.filter(id=request.user.id).exists()
        if isinstance(obj, Task):
            h = obj.household
            return h.created_by_id == request.user.id or h.members.filter(id=request.user.id).exists()
        if isinstance(obj, Invitation):
            h = obj.household
            return h.created_by_id == request.user.id or h.members.filter(id=request.user.id).exists()
        return False

class HouseholdViewSet(viewsets.ModelViewSet):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        u = self.request.user
        return Household.objects.filter(models.Q(created_by=u) | models.Q(members=u)).distinct()
    def perform_create(self, serializer):
        h = serializer.save(created_by=self.request.user)
        h.members.add(self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        u = self.request.user
        return Task.objects.filter(
            models.Q(household__created_by=u) | models.Q(household__members=u)).distinct()
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.is_completed = True
        task.completed_by = request.user
        task.completed_at = timezone.now()
        task.save(update_fields=["is_completed", "completed_by", "completed_at"])
        return Response(TaskSerializer(task).data)


class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        u = self.request.user
        return Invitation.objects.filter(
            models.Q(invitee=u) |
            models.Q(household__created_by=u) |
            models.Q(household__members=u)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(inviter=self.request.user)