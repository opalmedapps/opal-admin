"""
Module providing models for the users app.

Provides a custom user model based on Django's [django.contrib.auth.models.AbstractUser][].
For more information see the [Django documentation on customizing the user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)

Contains user types and a proxy model for each user type.
To facilitate dealing with user types, each proxy model has a dedicated model manager.

This is based on Two Scoops of Django, Section 22.3.

If a user type requires additional fields that are not common to all users,
a dedicated profile should be used. This is based on Two Scoops of Django, Section 22.2.3.
"""  # noqa: E501
from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import MinValueValidator, RegexValidator
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

    language = models.CharField(
        verbose_name=_('Language'),
        max_length=2,
        choices=Language.choices,
        default=Language.FRENCH,
    )
    phone_number = models.CharField(
        verbose_name=_('Phone Number'),
        max_length=16,
        blank=True,
        # Based on a suggestion from here: https://www.twilio.com/docs/glossary/what-e164
        validators=[RegexValidator(r'^\+[1-9]\d{6,14}$')],
        help_text=_('Write in E.164 format (+[countryCode][phoneNumber]), for example +15141234567'),
    )
    type = models.CharField(  # noqa: A003
        verbose_name=_('Type'),
        max_length=10,
        choices=UserType.choices,
        default=base_type,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_language_valid',  # noqa: WPS323
                check=models.Q(language__in=Language.values),
            ),
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
        verbose_name = _('Clinical Staff Member')
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


class CaregiverProfile(models.Model):
    """Profile for caregiver users."""

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
        limit_choices_to={'type': UserType.CAREGIVER},
    )
    legacy_id = models.PositiveIntegerField(
        verbose_name=_('Legacy ID'),
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Caregiver Profile')
        verbose_name_plural = _('Caregiver Profiles')

    def __str__(self) -> str:
        """
        Return the string representation of the associated user.

        Returns:
            the name of the associated user
        """
        return '{first} {last}'.format(first=self.user.first_name, last=self.user.last_name)
