"""
This module provides custom permissions for the Django REST framework.

These permissions are provided for the project and intended to be reused.
"""
from rest_framework import permissions


class CustomDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Custom DRF `DjangoModelPermissions` permission which is more restrictive.

    Restricts GET operations to require the `view` permission on the model.

    See: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions
    """

    # overriden from DjangoModelPermissions
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],  # noqa: WPS323
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],  # noqa: WPS323
        'PUT': ['%(app_label)s.change_%(model_name)s'],  # noqa: WPS323
        'PATCH': ['%(app_label)s.change_%(model_name)s'],  # noqa: WPS323
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],  # noqa: WPS323
    }
