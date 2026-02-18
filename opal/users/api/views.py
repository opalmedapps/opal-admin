# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides `UpdateAPIViews` for the `users` app REST APIs."""

from django.contrib.auth.models import Group

from rest_framework import generics

from opal.core.drf_permissions import FullDjangoModelPermissions

from ..models import Caregiver
from .serializers import GroupSerializer, UpdateCaregiverEmailSerializer


class ListGroupView(generics.ListAPIView[Group]):
    """REST API `ListAPIView` returning list of available groups."""

    model = Group
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (FullDjangoModelPermissions,)


class UserCaregiverUpdateView(generics.UpdateAPIView[Caregiver]):
    """View to update a caregiver."""

    permission_classes = (FullDjangoModelPermissions,)
    serializer_class = UpdateCaregiverEmailSerializer
    queryset = Caregiver.objects.filter(is_active=True)
    lookup_url_kwarg = 'username'
    lookup_field = 'username'
