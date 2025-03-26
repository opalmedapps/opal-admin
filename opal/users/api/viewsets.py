"""This module provides `ViewSets` for the users app."""

from typing import Type

from rest_framework import viewsets
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.serializers import BaseSerializer

from ...core.drf_permissions import CustomDjangoModelPermissions
from ..models import ClinicalStaff
from .serializers import UpdateClinicalStaffUserSerializer, UserClinicalStaffSerializer


class UserViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides `create`, `retrieve`, and `update` actions to clinical staff and groups.

    It uses username as the lookup field in `ClinicalStaff` model.
    """

    queryset = ClinicalStaff.objects.all()
    lookup_field = 'username'
    lookup_url_kwarg = 'username'
    serializer_classes = {
        'create': UserClinicalStaffSerializer,
        'retrieve': UpdateClinicalStaffUserSerializer,
        'update': UserClinicalStaffSerializer,
    }
    permission_classes = [CustomDjangoModelPermissions]

    default_serializer_class = UserClinicalStaffSerializer

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """
        Override get_serializer_class to return the corresponding serializer for each action.

        Returns:
            The expected serializer
        """
        return self.serializer_classes.get(self.action, self.default_serializer_class)
