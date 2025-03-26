"""Collection of API views used to handle ORMS authentication."""

from django.conf import settings

from dj_rest_auth.views import LoginView
from rest_framework.exceptions import PermissionDenied


class ORMSLoginView(LoginView):
    """
    Custom `LoginView` for the ORMS system.

    It overrides the default `login` method and adds the user's group check.
    """

    def login(self) -> None:
        """Check user's group and credentials.

        Only users that belong to the `ORMS_USER_GROUP` can login to the system.

        Accept the following POST parameters: username, password

        Returns REST Framework Token Object's key if authorized.

        Raises:
            PermissionDenied: if not authorized.
        """
        user = self.serializer.validated_data['user']

        if user.groups.filter(
            name=settings.ORMS_USER_GROUP,
        ).exists():
            super().login()
        else:
            raise PermissionDenied()
