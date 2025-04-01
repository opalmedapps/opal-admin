# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides Django REST framework serializers for User-specific models."""

from typing import Any

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password as auth_validate_password
from django.utils.translation import gettext

from rest_framework import serializers

from ..models import Caregiver, ClinicalStaff


class GroupSerializer(serializers.ModelSerializer[Group]):
    """
    Group serializer.

    This serializer is used to get group information according to the fields argument.
    """

    class Meta:
        model = Group
        fields = ('pk', 'name')


class UserCaregiverUpdateSerializer(serializers.ModelSerializer[Caregiver]):
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
        extra_kwargs = {
            'email': {'allow_blank': False, 'required': True},
        }


class ClinicalStaffDetailSerializer(serializers.ModelSerializer[ClinicalStaff]):
    """
    ClinicalStaff data serializer.

    The serializer is used to provide details of a clinical staff user.
    """

    class Meta:
        model = ClinicalStaff
        fields = [
            'username',
            'first_name',
            'last_name',
        ]


class UserClinicalStaffSerializer(serializers.ModelSerializer[ClinicalStaff]):
    """
    User ClinicalStaff serializer.

    The serializer is used to create a new clinical staff user and assign them to group(s).
    """

    password = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ClinicalStaff
        fields = ('username', 'password', 'password2', 'groups')

    def validate_password(self, password: str) -> str:
        """
        Validate that the password follows the password requirements.

        Raises a `ValidationError` for any violation.

        Args:
            password: the raw password

        Returns:
            the validated password
        """
        auth_validate_password(password)

        return password

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate all data.

        Verifies that the passwords are the same.

        Args:
            data: the request data

        Returns:
            the validated data

        Raises:
            ValidationError: if the passwords are not the same
        """
        if 'password' in data and 'password2' in data and data['password'] != data['password2']:
            raise serializers.ValidationError(gettext("The two password fields don't match."))

        return data

    def save(self, **kwargs: Any) -> ClinicalStaff:
        """
        Save the validated data.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the created or updated clinical staff instance
        """
        # handle passwords if provided
        if 'password' in self.validated_data:
            self.validated_data.pop('password2')
            self.validated_data['password'] = make_password(self.validated_data['password'])

        return super().save(**kwargs)


class UpdateClinicalStaffGroupSerializer(serializers.ModelSerializer[ClinicalStaff]):
    """Serializer to retrieve and update the clinical staff users' groups."""

    class Meta:
        model = ClinicalStaff
        fields = ('groups',)
