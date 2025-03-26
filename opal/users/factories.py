"""
Module providing model factories for user app models.

Inspired by:
    * https://adamj.eu/tech/2014/09/03/factory-boy-fun/
    * https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
"""
from django.template.defaultfilters import slugify

from factory import Faker, lazy_attribute
from factory.django import DjangoModelFactory

from . import models


def slugify_user(user: models.User) -> str:
    """
    Slugify the user based on the user's first and last name.

    Args:
        user: the user instance

    Returns:
        the slugified user as `<first_name>.<last_name>`
    """
    return slugify('{0}.{1}'.format(user.first_name, user.last_name))


class User(DjangoModelFactory):
    """Model factory to create [opal.users.models.User][] models."""

    class Meta:
        model = models.User
        django_get_or_create = ('username',)

    first_name = Faker('first_name')
    last_name = Faker('last_name')
    username = lazy_attribute(slugify_user)
    email = lazy_attribute(lambda user: '{0}@example.com'.format(user.username))


class Caregiver(User):
    """Model factory to create [opal.users.models.Caregiver][] models."""

    class Meta:
        model = models.Caregiver
