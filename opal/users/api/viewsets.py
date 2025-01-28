"""This module provides `ViewSets` for the users app."""
from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from config.settings.base import USER_MANAGER_GROUP_NAME

from ...core.drf_permissions import FullDjangoModelPermissions
from ..models import ClinicalStaff
from .serializers import UpdateClinicalStaffGroupSerializer, UserClinicalStaffSerializer


class UserViewSet(  # noqa: WPS215 (too many base classes)
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet[ClinicalStaff],
):
    """
    A viewset that provides `create`, `retrieve`, and `update` actions to clinical staff and groups.

    It uses username as the lookup field in `ClinicalStaff` model.
    """

    queryset = ClinicalStaff.objects.all()
    lookup_field = 'username'
    lookup_url_kwarg = 'username'
    default_serializer_class = UserClinicalStaffSerializer
    serializer_classes = {
        'create': UserClinicalStaffSerializer,
        'retrieve': UpdateClinicalStaffGroupSerializer,
        'update': UserClinicalStaffSerializer,
        'set_manager_user': UpdateClinicalStaffGroupSerializer,
        'unset_manager_user': UpdateClinicalStaffGroupSerializer,
    }
    permission_classes = (FullDjangoModelPermissions,)

    @action(detail=True, methods=['put'], url_path='set-manager-user')
    def set_manager_user(self, request: Request, username: str) -> Response:
        """
        Handle requests for setting a user group.

        Add the passed user to a predefined managers group.

        Args:
            request: HTTP request.
            username: user's username.

        Returns:
            HTTP response with response details.

        Raises:
            NotFound: if admin group is not found.
        """
        clinicalstaff_user = self.get_object()

        try:
            group = Group.objects.get(name=USER_MANAGER_GROUP_NAME)
        except ObjectDoesNotExist:
            raise NotFound(_('Manager group not found.'))

        clinicalstaff_user.groups.add(group.pk)
        clinicalstaff_user.save()
        return Response({'detail': _('User was added to the managers group successfully.')}, status=HTTPStatus.OK)

    @action(detail=True, methods=['put'], url_path='unset-manager-user')
    def unset_manager_user(self, request: Request, username: str) -> Response:
        """
        Handle requests for unsetting a user group.

        Remove the passed user from a predefined managers group.

        Args:
            request: HTTP request.
            username: user's username.

        Returns:
            HTTP response with response details.

        Raises:
            NotFound: if admin group is not found.
        """
        clinicalstaff_user = self.get_object()

        try:
            group = Group.objects.get(name=USER_MANAGER_GROUP_NAME)
        except ObjectDoesNotExist:
            raise NotFound(_('Manager group not found.'))

        clinicalstaff_user.groups.remove(group.pk)
        clinicalstaff_user.save()
        return Response({'detail': _('User was removed from the managers group successfully.')}, status=HTTPStatus.OK)

    @action(detail=True, methods=['put'], url_path='deactivate-user')
    def deactivate_user(self, request: Request, username: str = '') -> Response:
        """
        Handle requests for deactivating a user.

        Set the attribute `is_active` to false.

        Args:
            request: HTTP request.
            username: user's username.

        Returns:
            HTTP response with response details.
        """
        clinicalstaff_user = self.get_object()

        clinicalstaff_user.is_active = False
        clinicalstaff_user.save()
        return Response({'detail': _('User was deactivated successfully.')}, status=HTTPStatus.OK)

    @action(detail=True, methods=['put'], url_path='reactivate-user')
    def reactivate_user(self, request: Request, username: str = '') -> Response:
        """
        Handle requests for reactivating a user.

        Set the attribute `is_active` to true.

        Args:
            request: HTTP request.
            username: user's username.

        Returns:
            HTTP response with response details.
        """
        clinicalstaff_user = self.get_object()

        clinicalstaff_user.is_active = True
        clinicalstaff_user.save()
        return Response({'detail': _('User was reactivated successfully.')}, status=HTTPStatus.OK)

    def get_serializer_class(self) -> type[ModelSerializer[ClinicalStaff]]:
        """
        Override get_serializer_class to return the corresponding serializer for each action.

        Returns:
            The expected serializer
        """
        return self.serializer_classes.get(self.action, self.default_serializer_class)
