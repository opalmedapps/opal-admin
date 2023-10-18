"""This module provides `UpdateAPIViews` for the `users` app REST APIs."""
from django.contrib.auth.models import Group

from rest_framework import generics

from opal.core.drf_permissions import FullDjangoModelPermissions

from ..models import Caregiver
from .serializers import GroupSerializer, UserCaregiverUpdateSerializer


class ListGroupView(generics.ListAPIView):
    """REST API `ListAPIView` returning list of available groups."""

    model = Group
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [FullDjangoModelPermissions]


class UserCaregiverUpdateView(generics.UpdateAPIView):
    """Class handling update the user's caregiver."""

    permission_classes = [FullDjangoModelPermissions]
    serializer_class = UserCaregiverUpdateSerializer
    queryset = Caregiver.objects.filter(is_active=True)
    lookup_url_kwarg = 'username'
    lookup_field = 'username'
