"""This module provides `ViewSets` for the users app."""
from http import HTTPStatus
from typing import Type

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from config.settings.base import USER_MANAGER_GROUP_NAME

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
        'update': UpdateClinicalStaffUserSerializer,
        'set_manager_user': UpdateClinicalStaffUserSerializer,
    }
    permission_classes = [CustomDjangoModelPermissions]

    default_serializer_class = UserClinicalStaffSerializer

    @action(detail=True, methods=['post'])
    def set_manager_user(self, request: Request, username: str = '') -> Response:
        """
        Handle requests for setting a user group.

        Add the passed user to a predefined managers group.

        Args:
            request: Http request.
            username: user username.

        Returns:
            Http response with response details.
        """
        try:
            clinicalstaff_user = ClinicalStaff.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({'detail': _('user not found.')}, status=HTTPStatus.NOT_FOUND)

        try:
            group = Group.objects.get(name=USER_MANAGER_GROUP_NAME)
        except ObjectDoesNotExist:
            return Response({'detail': _('manager group not found.')}, status=HTTPStatus.NOT_FOUND)

        clinicalstaff_user.groups.add(group.pk)
        clinicalstaff_user.save()
        return Response({'detail': _('user was added to the managers group successfully.')}, status=HTTPStatus.OK)

    @action(detail=True, methods=['post'])
    def unset_manager_user(self, request: Request, username: str = '') -> Response:
        """
        Handle requests for unsetting a user group.

        Remove the passed user from a predefined managers group.

        Args:
            request: Http request.
            username: user username.

        Returns:
            Http response with response details.
        """
        try:
            clinicalstaff_user = ClinicalStaff.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({'detail': _('user not found.')}, status=HTTPStatus.NOT_FOUND)

        try:
            group = Group.objects.get(name=USER_MANAGER_GROUP_NAME)
        except ObjectDoesNotExist:
            return Response({'detail': _('manager group not found.')}, status=HTTPStatus.NOT_FOUND)

        clinicalstaff_user.groups.remove(group.pk)
        clinicalstaff_user.save()
        return Response({'detail': _('user was removed from the managers group successfully.')}, status=HTTPStatus.OK)

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """
        Override get_serializer_class to return the corresponding serializer for each action.

        Returns:
            The expected serializer
        """
        return self.serializer_classes.get(self.action, self.default_serializer_class)
