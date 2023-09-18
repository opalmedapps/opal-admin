"""This module provides Django REST framework serializers related to the `User` app's models."""
from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import Caregiver


class UserCaregiverUpdateSerializer(DynamicFieldsSerializer):
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
