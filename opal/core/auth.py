"""Authentication backends specific to the opal project."""
from collections import namedtuple
from http import HTTPStatus
from typing import Optional, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

import requests
from requests.exceptions import RequestException

from opal.users.models import User

UserModel: Type[User] = get_user_model()
UserData = namedtuple('UserData', ['email', 'first_name', 'last_name'])

#: Representation in API response when authentication was successful.
AUTHENTICATION_SUCCESS = '1'
#: Representation in API response when authentication was unsuccessful.
AUTHENTICATION_FAILURE = '0'


class FedAuthBackend(BaseBackend):
    """
    Authentication backend which authenticates against the provincial auth web service.

    The "Service d'authentification fédéré ENA" internally authenticates against an institution's ADFS.

    See: https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#writing-an-authentication-backend
    """

    # method defined as per Django doc with explicit args instead of **kwargs
    def authenticate(  # type: ignore[override]
        self,
        request: Optional[HttpRequest],
        username: Optional[str],
        password: Optional[str],
    ) -> Optional[User]:
        """
        Authenticate against the provincial auth web service.

        If the user does not exist yet, it will be added as a regular user
        and their username, email, first and last name recorded.

        Args:
            request: the authentication HTTP request
            username: the ADFS username of the user
            password: the ADFS password of the user

        Returns:
            the `User` instance, `None` if the user could not be authenticated
        """
        if username is not None and password is not None:
            # perform auth against fedauth service
            user_data = self._authenticate_fedauth(username, password)

            if user_data:
                # Look up existing user or create new user if it is the first time.
                try:
                    user: User = UserModel.objects.get(username=username)
                except UserModel.DoesNotExist:
                    user = UserModel(username=username)

                    user.email = user_data.email
                    user.first_name = user_data.first_name
                    user.last_name = user_data.last_name
                    # There's no need to set a password since it is stored in ADFS.
                    # Mark it as unusable:
                    # https://docs.djangoproject.com/en/dev/ref/contrib/auth/#django.contrib.auth.models.User.set_unusable_password
                    user.set_unusable_password()

                    user.save()
                return user

        return None

    def get_user(self, user_id: int) -> Optional[User]:  # noqa: WPS615
        """
        Retrieve the user with the given user ID.

        Args:
            user_id: the ID of the user model instance

        Returns:
            the `User` instance if the user exists, otherwise `None`
        """
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

    def _authenticate_fedauth(self, username: str, password: str) -> Optional[UserData]:
        """
        Perform the request to the fed auth web service.

        Args:
            username: the username
            password: the password

        Returns:
            the user data extracted from the web service response
            `None` if the authentication was unsuccessful
        """
        try:
            response = requests.post(
                settings.FEDAUTH_API_ENDPOINT,
                {
                    'institution': settings.FEDAUTH_INSTITUTION,
                    'uid': username,
                    'pwd': password,
                },
            )
        except RequestException as exc:
            # TODO: add logging
            print(exc)
        else:
            return self._parse_response(response)

        return None

    def _parse_response(self, response: requests.Response) -> Optional[UserData]:
        """
        Parse the response from the fed auth web service.

        Extract the relevant user data from the response if the authentication was successful.

        Args:
            response: the HTTP response from the web service

        Returns:
            the user data extracted from the web service response
            `None` if the authentication was unsuccessful
        """
        if response.status_code == HTTPStatus.OK:
            auth_data = response.json()

            # key 'authenticate' corresponds to 'statusCode' except it is the inverse
            # authenticate: 0 = not authenticated, 1 = authenticated
            # statusCode: 0 = no error, 1 = error
            #
            # if the data does not contain the key (e.g., in an empty return), handle as not authenticated
            if (
                auth_data.get('authenticate', AUTHENTICATION_FAILURE) == AUTHENTICATION_SUCCESS
                and all(key in auth_data for key in ('mail', 'givenName', 'sn'))
            ):
                email = auth_data['mail']
                first_name = auth_data['givenName']
                last_name = auth_data['sn']

                return UserData(email, first_name, last_name)

        return None
