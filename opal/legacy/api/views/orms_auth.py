"""Collection of API views used to handle ORMS authentication."""
from django.conf import settings

from dj_rest_auth.views import LoginView
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsORMSUser
from opal.users.api.serializers import ClinicalStaffDetailSerializer
from opal.users.models import ClinicalStaff


class ORMSLoginView(LoginView):
    """
    Custom `LoginView` for the ORMS system.

    It overrides the default `login` method and adds the user's group check.
    """

    def login(self) -> None:
        """Check user's group and credentials.

        Only superusers and users that belong to the `ORMS_GROUP_NAME` can login to the system.

        Accept the following POST parameters: username, password

        Returns REST Framework Token Object's key if authorized.

        Raises:
            PermissionDenied: if not authorized.
        """
        user = self.serializer.validated_data['user']

        if user.is_superuser or user.groups.filter(
            name=settings.ORMS_GROUP_NAME,
        ).exists():
            super().login()
        else:
            raise PermissionDenied()


@extend_schema(
    responses={
        200: ClinicalStaffDetailSerializer,
    },
)
class ORMSValidateView(APIView):
    """
    Custom `ValidateView` for the ORMS system.

    It checks user authentication and the user's group.
    """

    permission_classes = (IsORMSUser,)

    def get(self, request: Request) -> Response:
        """
        Validate if the user is authenticated and user belongs to ORMS user group.

        Raises `PermissionDenied` if the user has no permission.
        I.e., the user is not a superuser or not part of the ORMS users group.

        Args:
            request: the HTTP request.

        Returns:
            Http response with caregiver username and status code.
        """
        user: ClinicalStaff = request.user  # type: ignore[assignment]

        return Response(
            data=ClinicalStaffDetailSerializer(user).data,
        )
