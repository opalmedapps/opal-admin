"""Collection of API views used to handle ORMS authentication."""

from django.conf import settings

from dj_rest_auth.views import LoginView
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.users.api.serializers import UserCaregiverUpdateSerializer
from opal.users.models import Caregiver


class ORMSLoginView(LoginView):
    """
    Custom `LoginView` for the ORMS system.

    It overrides the default `login` method and adds the user's group check.
    """

    def login(self) -> None:
        """Check user's group and credentials.

        Only users that belong to the `ORMS_GROUP_NAME` can login to the system.

        Accept the following POST parameters: username, password

        Returns REST Framework Token Object's key if authorized.

        Raises:
            PermissionDenied: if not authorized.
        """
        user = self.serializer.validated_data['user']

        if user.groups.filter(
            name=settings.ORMS_GROUP_NAME,
        ).exists():
            super().login()
        else:
            raise PermissionDenied()


class ORMSValidateView(APIView):
    """
    Custom `ValidateView` for the ORMS system.

    It checks user authentication and the user's group.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:  # noqa: WPS210
        """
        Validate if the user is authenticated and user belongs to ORMS user group.

        Args:
            request: the HTTP request.

        Raises:
            PermissionDenied: if no permission.

        Returns:
            Http response with empty message.
        """
        user = request.user

        if user.is_authenticated and not user.groups.filter(
            name=settings.ORMS_GROUP_NAME,
        ).exists():
            raise PermissionDenied()

        return Response(
            UserCaregiverUpdateSerializer(
                Caregiver.objects.first(),
            ).data,
            status=status.HTTP_200_OK,
        )
