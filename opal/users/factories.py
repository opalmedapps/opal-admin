"""
Module providing model factories for user app models.

Inspired by:

  * https://adamj.eu/tech/2014/09/03/factory-boy-fun/
  * https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
"""
from django.contrib.auth.hashers import make_password
from django.template.defaultfilters import slugify

from factory import Faker, LazyFunction, lazy_attribute
from factory.django import DjangoModelFactory

from . import models


def _slugify_user(user: models.User) -> str:
    """
    Slugify the user based on a fake username.

    Args:
        user: the user instance

    Returns:
        the slugified username
    """
    return slugify(Faker('username'))


class User(DjangoModelFactory):
    """Model factory to create [opal.users.models.User][] models."""

    class Meta:
        model = models.User
        django_get_or_create = ('username',)

    first_name = 'Marge'
    last_name = 'Simpson'
    username = lazy_attribute(_slugify_user)
    # produce a different hash for the same password for each user
    password = LazyFunction(lambda: make_password('thisisatest'))
    email = lazy_attribute(lambda user: '{0}@example.com'.format(user.username))


class Caregiver(User):
    """Model factory to create [opal.users.models.Caregiver][] models."""

    class Meta:
        model = models.Caregiver
