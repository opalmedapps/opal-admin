# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Authentication backends specific to the opal project."""

import logging
from collections import namedtuple
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

import requests
from requests.exceptions import RequestException

from opal.users.models import User

UserModel: type[User] = get_user_model()
UserData = namedtuple('UserData', ['email', 'first_name', 'last_name'])

#: Representation in API response when authentication was successful.
AUTHENTICATION_SUCCESS = '1'
#: Representation in API response when authentication was unsuccessful.
AUTHENTICATION_FAILURE = '0'

LOGGER = logging.getLogger(__name__)


class FedAuthBackend(BaseBackend):
    """
    Authentication backend which authenticates against the provincial auth web service.

    The "Service d'authentication fédéré ENA" internally authenticates against an institution's ADFS.

    See: https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#writing-an-authentication-backend
    """

    # method defined as per Django doc with explicit args instead of **kwargs
    def authenticate(  # type: ignore[override]
        self,
        request: HttpRequest | None,
        username: str | None,
        password: str | None,
    ) -> User | None:
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
                # Look up existing user and update any fields if necessary.
                # Note that new user creation was disabled
                user = UserModel.objects.filter(username=username).first()

                if user:
                    # augment user data if it is not present with data from ADFS
                    # required for users added via the legacy OpalAdmin which doesn't capture email, first and last name
                    self._update_user(user, user_data)

                    return user

        return None

    def get_user(self, user_id: int) -> User | None:
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

    def _authenticate_fedauth(self, username: str, password: str) -> UserData | None:
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
                timeout=10,
            )
        except RequestException:
            LOGGER.exception('error while requesting the fed auth API')
        else:
            return self._parse_response(response)

        return None

    def _parse_response(self, response: requests.Response) -> UserData | None:
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
            if auth_data.get('authenticate', AUTHENTICATION_FAILURE) == AUTHENTICATION_SUCCESS:
                email = auth_data.get('mail', '')
                first_name = auth_data.get('givenName', '')
                last_name = auth_data.get('sn', '')

                return UserData(email, first_name, last_name)

        return None

    def _create_user(self, username: str, user_data: UserData) -> User:
        """
        Create a new user.

        Args:
            username: the ADFS username of the user
            user_data: the user data received from the ADFS

        Returns:
            the new `User` instance
        """
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

    def _update_user(self, user: User, user_data: UserData) -> None:
        """
        Update the existing user if it is missing data.

        Args:
            user: the existing user instance
            user_data: the user data received from the ADFS
        """
        needs_save = False

        if not user.first_name and user_data.first_name:
            user.first_name = user_data.first_name
            needs_save = True
        if not user.last_name and user_data.last_name:
            user.last_name = user_data.last_name
            needs_save = True
        if not user.email and user_data.email:
            user.email = user_data.email
            needs_save = True

        if needs_save:
            user.save()
