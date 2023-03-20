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
from typing import Any, TypeAlias

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


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
    UserType: TypeAlias = UserType

    base_type = UserType.CLINICAL_STAFF

    language = models.CharField(
        verbose_name=_('Language'),
        max_length=2,
        choices=Language,
        # use the language code of the first language
        default=Language[0][0],
    )
    phone_number = models.CharField(
        verbose_name=_('Phone Number'),
        max_length=22,
        blank=True,
        # Based on a suggestion from here: https://www.twilio.com/docs/glossary/what-e164
        validators=[RegexValidator(r'^\+[1-9]\d{6,14}(x\d{1,5})?$')],
        help_text=_('Format: +<countryCode><phoneNumber> (for example +15141234567) with an optional extension "x123"'),
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
                # determine the language codes from the list of tuples
                check=models.Q(language__in=[language[0] for language in Language]),
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

    objects = ClinicalStaffManager()

    class Meta:
        proxy = True
        verbose_name = _('Clinical Staff Member')
        verbose_name_plural = _('Clinical Staff')


class CaregiverManager(UserManager[User]):
    """
    UserManager for `Caregiver` users.

    Provides a queryset limited to users of type `UserType.CAREGIVER`.
    """

    def get_queryset(self) -> models.QuerySet[User]:
        """
        Return a new QuerySet filtered by users of type `UserType.ClinicalStaff`.

        Returns:
            a QuerySet of users
        """
        queryset = super().get_queryset()
        return queryset.filter(type=UserType.CAREGIVER)


class Caregiver(User):
    """Proxy user model for the caregiver user type."""

    base_type = UserType.CAREGIVER

    objects = CaregiverManager()

    class Meta:
        proxy = True
        verbose_name = _('Caregiver')
        verbose_name_plural = _('Caregivers')
