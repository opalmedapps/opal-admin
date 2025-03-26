"""This module provides `UpdateAPIViews` for the `users` app REST APIs."""
from django.db.models.query import QuerySet

from rest_framework.generics import UpdateAPIView, get_object_or_404

from opal.core.drf_permissions import CustomDjangoModelPermissions

from ..api.serializers import UserCaregiverUpdateSerializer
from ..models import Caregiver, User


class UserCaregiverUpdateView(UpdateAPIView):
    """Class handling update the user's caregiver."""

    permission_classes = [CustomDjangoModelPermissions]
    serializer_class = UserCaregiverUpdateSerializer
    lookup_url_kwarg = 'username'
    lookup_field = 'username'

    def get_queryset(self) -> QuerySet[User]:
        """Provide the desired object or fails with 404 error.

        Returns:
            Device object or 404.
        """
        serializer = self.serializer_class(
            data=self.request.data,
        )
        serializer.is_valid(raise_exception=True)
        register_data = serializer.validated_data
        username = self.kwargs['username']
        caregiver = get_object_or_404(Caregiver.objects.filter(username=username))
        caregiver.email = register_data['email']
        caregiver.save()
        return Caregiver.objects.filter(username=username)
