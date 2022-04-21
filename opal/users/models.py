"""
Module providing models for the users app.

Provides a custom user model based on Django's [django.contrib.auth.models.AbstractUser][].
For more information see the [Django documentation on customizing the user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)
"""  # noqa: E501
from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.TextChoices):
    """The available language options for users."""

    ENGLISH = 'EN', _('English')
    FRENCH = 'FR', _('French')


class UserType(models.TextChoices):
    """Choice of user types of which a user can be one of."""

    CLINICAL_STAFF = 'CLINICAL', _('Clinical Staff')
    CAREGIVER = 'CAREGIVER', _('Caregiver')


class User(AbstractUser):
    """Default custom user model."""

    base_type = UserType.CLINICAL_STAFF

    type = models.CharField(  # noqa: A003
        verbose_name=_('Type'),
        max_length=10,
        choices=UserType.choices,
        default=base_type,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',  # noqa: WPS323
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


class ClinicalStaffManager(UserManager):
    """
    UserManager for `ClinicalStaff` users.

    Provides a queryset limited to users of type `UserType.ClinicalStaff`.
    """

    def get_queryset(self, *args: Any, **kwargs: Any) -> models.QuerySet[User]:
        """
        Return a new QuerySet filtered by users of type `UserType.ClinicalStaff`.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            a QuerySet of users
        """
        queryset = super().get_queryset(*args, **kwargs)
        return queryset.filter(type=UserType.CLINICAL_STAFF)


class ClinicalStaff(User):
    """Proxy user model for the clinical staff user type."""

    base_type = UserType.CLINICAL_STAFF

    objects = ClinicalStaffManager()

    class Meta:
        proxy = True
        verbose_name = _('Clinical Staff')
        verbose_name_plural = _('Clinical Staff')


class CaregiverManager(UserManager):
    """
    UserManager for `Caregiver` users.

    Provides a queryset limited to users of type `UserType.CAREGIVER`.
    """

    def get_queryset(self, *args: Any, **kwargs: Any) -> models.QuerySet[User]:
        """
        Return a new QuerySet filtered by users of type `UserType.ClinicalStaff`.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            a QuerySet of users
        """
        queryset = super().get_queryset(*args, **kwargs)
        return queryset.filter(type=UserType.CAREGIVER)


class Caregiver(User):
    """Proxy user model for the caregiver user type."""

    base_type = UserType.CAREGIVER

    objects = CaregiverManager()

    class Meta:
        proxy = True
        verbose_name = _('Caregiver')
        verbose_name_plural = _('Caregivers')
