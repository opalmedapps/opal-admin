"""Module providing API views for the `users` app."""
from django.contrib.auth.models import Group

from rest_framework import generics

from ...core.drf_permissions import CustomDjangoModelPermissions
from .serializers import GroupSerializer


class ListGroupView(generics.ListAPIView):
    """REST API `ListAPIView` returning list of available groups."""

    model = Group
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = None
    permission_classes = [CustomDjangoModelPermissions]
