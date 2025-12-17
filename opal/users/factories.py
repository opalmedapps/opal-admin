# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module providing model factories for user app models.

Inspired by:

  * https://adamj.eu/tech/2014/09/03/factory-boy-fun/
  * https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
"""

from typing import TypeVar

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group

from factory import Faker, LazyFunction, lazy_attribute
from factory.django import DjangoModelFactory

from . import models

_T = TypeVar('_T', bound=models.User, default=models.User)


class User(DjangoModelFactory[_T]):
    """Model factory to create [opal.users.models.User][] models."""

    class Meta:
        model = models.User
        django_get_or_create = ('username',)

    first_name = 'Marge'
    last_name = 'Simpson'
    username = Faker('user_name')
    # produce a different hash for the same password for each user
    password = LazyFunction(lambda: make_password('thisisatest'))
    email = lazy_attribute(lambda user: f'{user.username}@example.com')
    phone_number = ''


class Caregiver(User[models.Caregiver]):
    """Model factory to create [opal.users.models.Caregiver][] models."""

    class Meta:
        model = models.Caregiver


class ClinicalStaff(User[models.ClinicalStaff]):
    """Model factory to create [opal.users.models.ClinicalStaff][] models."""

    class Meta:
        model = models.ClinicalStaff


class GroupFactory(DjangoModelFactory[Group]):
    """Model factory to create Groups."""

    class Meta:
        model = Group

    name = 'System Administrators'
