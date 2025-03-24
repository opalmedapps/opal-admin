# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module providing models for the users app.

Provides a custom user model based on Django's [django.contrib.auth.models.AbstractUser][].
For more information see the [Django documentation on customizing the user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)

Contains user types and a proxy model for each user type.
To facilitate dealing with user types, each proxy model has a dedicated model manager.

This is based on Two Scoops of Django, Section 22.3.

If a user type requires additional fields that are not common to all users,
a dedicated profile should be used. This is based on Two Scoops of Django, Section 22.2.3.
"""

from typing import Any, ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from config.settings.base import ADMIN_GROUP_NAME


class UserType(models.TextChoices):
    """Choice of user types of which a user can be one of."""

    CLINICAL_STAFF = 'CLINICAL', _('Clinical Staff')
    CAREGIVER = 'CAREGIVER', _('Caregiver')


# Use the list of languages from the project's settings
# TODO: Switch to StrEnum using functional API when switching to Python 3.11
# see: https://docs.python.org/3.11/howto/enum.html#strenum
Language = settings.LANGUAGES


class User(AbstractUser):
    """Default custom user model."""

    # TextChoices need to be defined outside to use them in constraints
    # define them as class attributes for easier access
    # see: https://stackoverflow.com/q/71522816
    UserType = UserType

    base_type = UserType.CLINICAL_STAFF

    language = models.CharField(
        verbose_name=_('Language'),
        max_length=2,
        choices=Language,
        # use the language code of the first language
        default=Language[0][0],
    )
    phone_number = PhoneNumberField(
        verbose_name=_('Phone Number'),
        blank=True,
    )
    type = models.CharField(
        verbose_name=_('Type'),
        max_length=10,
        choices=UserType.choices,
        default=base_type,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_language_valid',
                # determine the language codes from the list of tuples
                check=models.Q(language__in=[language[0] for language in Language]),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',
                check=models.Q(type__in=UserType.values),
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the current instance.

        If a new user is saved, the `type` field is set based on the `base_type` property.
        Subclasses (proxy models) should change the `base_type` to the type they represent.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        if not self.pk:
            self.type = self.base_type

        super().save(*args, **kwargs)


class ClinicalStaffManager(UserManager[User]):
    """
    UserManager for `ClinicalStaff` users.

    Provides a queryset limited to users of type `UserType.ClinicalStaff`.
    """

    def get_queryset(self) -> models.QuerySet[User]:
        """
        Return a new QuerySet filtered by users of type `UserType.ClinicalStaff`.

        Returns:
            a QuerySet of users
        """
        queryset = super().get_queryset()
        return queryset.filter(type=UserType.CLINICAL_STAFF)


class ClinicalStaff(User):
    """Proxy user model for the clinical staff user type."""

    base_type = UserType.CLINICAL_STAFF

    objects: ClassVar[UserManager['ClinicalStaff']] = ClinicalStaffManager()  # type: ignore[assignment]

    class Meta:
        proxy = True
        verbose_name = _('Clinical Staff Member')
        verbose_name_plural = _('Clinical Staff')


class CaregiverManager(UserManager['User']):
    """
    UserManager for `Caregiver` users.

    Provides a queryset limited to users of type `UserType.CAREGIVER`.
    """

    def get_queryset(self) -> models.QuerySet[User]:
        """
        Return a new QuerySet filtered by users of type `UserType.ClinicalStaff`.

        Returns:
            a QuerySet of caregivers
        """
        queryset = super().get_queryset()
        return queryset.filter(type=UserType.CAREGIVER)


class Caregiver(User):
    """Proxy user model for the caregiver user type."""

    base_type = UserType.CAREGIVER

    objects: ClassVar[UserManager['Caregiver']] = CaregiverManager()  # type: ignore[assignment]

    class Meta:
        proxy = True
        verbose_name = _('Caregiver')
        verbose_name_plural = _('Caregivers')


@receiver(signal=m2m_changed, sender=ClinicalStaff.groups.through)
def post_save_user_signal_handler(
    instance: ClinicalStaff,
    action: str,
    model: type[models.Model],
    pk_set: set[int],
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Post save function that is triggered by a signal once a change in the `users.groups` relationship is performed.

    The goal of this function is to set `is_staff` and `is_superuser` to True when a user is added to admin_group.

    Args:
        instance: the user object that underwent the change
        action: the action name that triggers the signal `post_add`, `post_remove`
        model: the model that triggers the signal
        pk_set: the pk of the record that was added/removed to the model
        args: argument sent with the request
        kwargs: extra keyword arguments
    """
    actions_map = {
        'post_add': (True, True),
        'post_remove': (False, False),
    }

    if model == Group and instance.type == UserType.CLINICAL_STAFF:
        administrators_group = Group.objects.filter(name=ADMIN_GROUP_NAME).first()
        privileges = actions_map.get(action)
        if administrators_group and administrators_group.pk in pk_set and privileges:
            is_superuser, is_staff = privileges
            instance.is_superuser = is_superuser
            instance.is_staff = is_staff

    instance.save()
