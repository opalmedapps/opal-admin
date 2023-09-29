"""This module provides Django REST framework serializers for User-specific models."""
from django.contrib.auth.models import Group

from rest_framework import serializers

from ..models import Caregiver, ClinicalStaff


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


class UserClinicalStaffSerializer(serializers.ModelSerializer):
    """
    User ClinicalStaff serializer.

    The serializer is used to create new clinical staff user and assigned them to group(s).
    """

    class Meta:
        model = ClinicalStaff
        fields = ('username', 'groups')


class UpdateClinicalStaffUserSerializer(serializers.ModelSerializer):
    """Serializer to retrieve and update the clinical staff users' groups."""

    class Meta:
        model = ClinicalStaff
        fields = ('groups',)
