"""Module providing models for the caregivers app."""

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


class CaregiverProfile(models.Model):
    """Profile for caregiver users."""

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
        limit_choices_to={'type': User.UserType.CAREGIVER},
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


class RegistrationCodeStatus(models.TextChoices):
    """Valid choice of status of a `RegistrationCode`."""

    NEW = 'NEW', _('New')
    REGISTERED = 'REG', _('Registered')
    EXPIRED = 'EXP', _('Expired')
    BLOCKED = 'BLK', _('Blocked')


class RegistrationCode(models.Model):
    """Model Registration Code."""

    relationship = models.ForeignKey(
        # Using string model references to avoid circular import
        to='patients.Relationship',
        verbose_name=_('Relationship'),
        related_name='registration_codes',
        on_delete=models.CASCADE,
    )

    code = models.CharField(
        verbose_name=_('Code'),
        max_length=12,
        validators=[MinLengthValidator(12)],
        unique=True,
    )

    status = models.CharField(
        verbose_name=_('Status'),
        choices=RegistrationCodeStatus.choices,
        default=RegistrationCodeStatus.NEW,
        max_length=3,
    )

    creation_date = models.DateField(
        verbose_name=_('Creation Date'),
        auto_now_add=True,
    )

    attempts = models.PositiveIntegerField(
        verbose_name=_('Attempts'),
        default=0,
    )

    email_verification_code = models.CharField(
        verbose_name=_('Email Verification Code'),
        max_length=6,
        validators=[MinLengthValidator(6)],
    )

    class Meta:
        verbose_name = _('Registration Code')
        verbose_name_plural = _('Registration Codes')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_status_valid',  # noqa: WPS323
                check=models.Q(status__in=RegistrationCodeStatus.values),
            ),
        ]

    def __str__(self) -> str:
        """
        Return the string registration code of the associated relationship.

        Returns:
            the string registration code of the associated relationship
        """
        return 'Code: {code} (Status: {status})'.format(
            code=self.code,
            status=self.status,
        )
