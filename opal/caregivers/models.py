"""Module providing models for the caregivers app."""
from uuid import uuid4

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


class CaregiverProfile(models.Model):
    """Profile for caregiver users."""

    uuid = models.UUIDField(
        verbose_name=_('UUID'),
        unique=True,
        default=uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
        limit_choices_to={'type': User.UserType.CAREGIVER},
    )
    legacy_id = models.PositiveIntegerField(
        verbose_name=_('Legacy ID'),
        validators=[MinValueValidator(1)],
        unique=True,
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
        return f'{self.user.last_name}, {self.user.first_name}'


class SecurityQuestion(models.Model):  # type: ignore[django-manager-missing]
    """Security question model."""

    title = models.CharField(
        verbose_name=_('Title'),
        max_length=100,
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
    )

    class Meta:
        verbose_name = _('Security Question')
        verbose_name_plural = _('Security Questions')

    def __str__(self) -> str:
        """Return the question text.

        Returns:
            the question text.
        """
        return self.title


class SecurityAnswer(models.Model):
    """Security answer model."""

    question = models.CharField(
        verbose_name=_('Question'),
        max_length=100,
    )

    user = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver Profile'),
        related_name='security_answers',
        on_delete=models.CASCADE,
    )

    answer = models.CharField(
        verbose_name=_('Answer'),
        max_length=128,
    )

    class Meta:
        verbose_name = _('Security Answer')
        verbose_name_plural = _('Security Answers')

    def __str__(self) -> str:
        """Return the question.

        Returns:
            the question.
        """
        return self.question


class DeviceType(models.TextChoices):
    """Choices of 'type' for the [opal.caregivers.models.Device][] model."""

    BROWSER = 'WEB', _('Browser')
    IOS = 'IOS', _('iOS')
    ANDROID = 'AND', _('Android')


class Device(models.Model):
    """Mobile device used by a caregiver to log into the app."""

    caregiver = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver Profile'),
        related_name='devices',
        on_delete=models.CASCADE,
    )

    type = models.CharField(  # noqa: A003
        verbose_name=_('Device Type'),
        max_length=3,
        choices=DeviceType.choices,
    )

    device_id = models.CharField(
        verbose_name=_('Device ID'),
        max_length=100,
    )

    is_trusted = models.BooleanField(
        verbose_name=_('Trusted Device'),
        default=False,
    )

    push_token = models.CharField(
        verbose_name=_('Push Token'),
        max_length=256,
        blank=True,
    )

    modified = models.DateTimeField(
        verbose_name=_('Last Modified'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',  # noqa: WPS323
                check=models.Q(type__in=DeviceType.values),
            ),
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_caregiver_device',  # noqa: WPS323
                fields=['caregiver_id', 'device_id'],
            ),
        ]

    def __str__(self) -> str:
        """
        Represent a Device as a string, showing its device_id.

        Returns:
            The string representation of a Device.
        """
        return self.device_id


class RegistrationCodeStatus(models.TextChoices):
    """Valid choice of status of a `RegistrationCode`."""

    NEW = 'NEW', _('New')
    REGISTERED = 'REG', _('Registered')
    EXPIRED = 'EXP', _('Expired')
    BLOCKED = 'BLK', _('Blocked')


class RegistrationCode(models.Model):
    """A Registration Code belonging to an [Patients][location of the model] with its specific properties."""

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

    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        auto_now_add=True,
    )

    attempts = models.PositiveIntegerField(
        verbose_name=_('Attempts'),
        default=0,
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
        Return the textual representation of the registration code.

        Returns:
            the string representation of the registration code
        """
        return self.code


class EmailVerification(models.Model):
    """A model to save verification codes along with its properties."""

    caregiver = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver Profile'),
        related_name='email_verifications',
        on_delete=models.CASCADE,
    )

    code = models.CharField(
        verbose_name=_('Verification Code'),
        max_length=6,
        validators=[MinLengthValidator(6)],
    )

    email = models.EmailField(
        verbose_name=_('Email'),
    )

    is_verified = models.BooleanField(
        verbose_name=_('Verified'),
        default=False,
    )

    sent_at = models.DateTimeField(
        null=True,
    )

    class Meta:
        verbose_name = _('Email Verification')
        verbose_name_plural = _('Email Verifications')

    def __str__(self) -> str:
        """
        Return the string email and its status.

        Returns:
            the string email and its status
        """
        return self.code
