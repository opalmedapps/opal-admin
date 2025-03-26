from http import HTTPStatus
from typing import Any, Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

import requests

UserModel: Type[User] = get_user_model()


class FedAuthBackend(BaseBackend):
    """
    Authenticate against the provincial auth web service.

    The "Service d'authentification fédéré ENA" internally authenticates against an institution's ADFS.
    If a user does not exist yet, it will be added as a regular user
    and their username, email, first and last name recorded.
    """

    def authenticate(self, request, username=None, password=None, **kwargs: Any) -> Optional[User]:
        print('authenticate using fed auth')
        if username is not None and password is not None:
            # perform auth against fedauth service
            if self._authenticate_fedauth(username, password):
                print('success')
                try:
                    user: User = UserModel.objects.get(username=username)
                except UserModel.DoesNotExist:
                    # Create a new user.
                    # There's no need to set a password since it is stored in ADFS.
                    user = UserModel(username=username)
                    # user.email =
                    # user.first_name =
                    # user.last_name =
                    user.is_staff = True
                    user.save()
                print(user)
                return user

        return None

    def get_user(self, user_id) -> Optional[User]:
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

    def _authenticate_fedauth(self, username: str, password: str) -> bool:
        response = requests.post(
            'https://fedauthfcp.rtss.qc.ca/fedauth/wsapi/login',
            {
                'institution': '06-ciusss-cusm',
                'uid': username,
                'pwd': password
            },
        )

        print(response)

        return self._parse_response(response)

    def _parse_response(self, response: requests.Response):
        if response.status_code == HTTPStatus.OK:
            data = response.json()

            # if the data does not contain the key, use the unauthenticated indication
            if data.get('authenticate', '0') == '1':
                return True

        return False
