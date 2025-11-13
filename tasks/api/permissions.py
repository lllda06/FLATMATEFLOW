from rest_framework import permissions
from tasks.models import Household, Task, Invitation

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