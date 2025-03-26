"""This module provides Django REST framework serializers for User-specific models."""
from django.contrib.auth.models import Group

from rest_framework import serializers

from ..models import Caregiver


class GroupSerializer(serializers.ModelSerializer):
    """
    Group serializer.

    This serializer is used to get group information according to the fields argument.
    """

    class Meta:
        model = Group
        fields = ('pk', 'name')


class UserCaregiverUpdateSerializer(serializers.ModelSerializer):
    """
    User caregiver serializer.

    The serializer, which inherits from core.api.serializers.DynamicFieldsSerializer,
    is used to update user caregiver email address.
    """

    class Meta:
        model = Caregiver
        fields = [
            'email',
        ]
        extra_kwargs = {'email': {'allow_blank': False, 'required': True}}
