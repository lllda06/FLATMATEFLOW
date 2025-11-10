from rest_framework import serializers
from django.conf import settings
from django.apps import apps
from tasks.models import Household, Task, Invitation

User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')

class HouseholdSerializer(serializers.ModelSerializer):
    created_by = UserShortSerializer(read_only=True)
    members = UserShortSerializer(read_only=True, many=True)

    class Meta:
        model = Household
        fields = ('id', 'name', 'description', 'gift', 'created_by', 'members', 'created_at')

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserShortSerializer(read_only=True)
    completed_by = UserShortSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'household', 'title', 'description', 'points', 'assigned_to',
        'is_completed', 'completed_by', 'created_at', 'completed_at')

class InvitationSerializer(serializers.ModelSerializer):
    inviter = UserShortSerializer(read_only=True)
    invitee = UserShortSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = (
            'id', 'token', 'household', 'inviter', 'invitee',
            'status', 'created_at', 'expires_at', 'accepted_at'
        )
        read_only_fields = ('token', 'status', 'created_at', 'accepted_at')