"""Module providing models for the caregivers app."""

from django.core.exceptions import ValidationError
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
    """Pre defined status of registration code."""

    NEW = 'NEW', _('New')
    REGISTERED = 'REG', _('Registered')
    EXPIRED = 'EXP', _('Expired')
    BLOCKED = 'BLK', _('Blocked')


class RegistrationCode(models.Model):
    """Model Registration Code."""

    relationship = models.ForeignKey(
        to='patients.Relationship',  # Using string model references to avoid circular import
        verbose_name=_('Relationship'),
        related_name='registrationcodes',
        on_delete=models.CASCADE,
    )

    code = models.CharField(
        verbose_name=_('Registration Code Value'),
        max_length=12,
        validators=[MinLengthValidator(12)],
    )

    status = models.CharField(
        verbose_name=_('Relationship Code Status'),
        choices=RegistrationCodeStatus.choices,
        default=RegistrationCodeStatus.NEW,
        max_length=3,
    )

    creation_date = models.DateField(
        verbose_name=_('Registration Code Creation Date'),
        auto_now_add=True,
    )

    attempts = models.PositiveIntegerField(
        verbose_name=_('Registration Code Attemps'),
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
        return 'code: {code}, status: {status}, {relationship}'.format(
            code=self.code,
            status=self.status,
            relationship=self.relationship,
        )

    def clean(self) -> None:
        """Validate the length of registration code and the length of email verification code.

        Raises:
            ValidationError: the error shows when the code is greater than or less than the limit length
        """
        length_regis_code = len(self.code)
        length_verif_code = len(self.email_verification_code)
        if self.code is not None and (length_regis_code > 12 or length_regis_code < 12):
            raise ValidationError({'Registration Code': _('Code length should be equal to 12.')})

        if self.email_verification_code is not None and (length_verif_code > 6 or length_verif_code < 6):
            raise ValidationError({'Email Verification Code': _('Code length should be equal to 6.')})
