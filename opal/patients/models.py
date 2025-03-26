"""Module providing models for the patients app."""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.hospital_settings.models import RelationshipType
from opal.users.models import CaregiverProfile


class RelationshipStatus(models.TextChoices):
    """Choice of relationship status."""

    PENDING = 'PEN', _('PENDING')
    CONFIRMED = 'CON', _('CONFIRMED')
    DENIED = 'DEN', _('DENIED')
    EXPIRED = 'EXP', _('EXPIRED')
    REVOKED = 'REP', _('EXPIRED')


class Patient(models.Model):
    """patient model."""

    first_name = models.CharField(
        verbose_name=_('First Name'),
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name=_('Last Name'),
        max_length=150,
        blank=True,
    )
    birth_day = models.DateField()
    caregivers = models.ManyToManyField(
        verbose_name=_('Caregivers'),
        related_name='patients',
        to=CaregiverProfile,
        through='Relationship',
    )
    legacy_id = models.PositiveIntegerField(
        verbose_name=_('Legacy ID'),
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')

    def __str__(self) -> str:
        """
        Return the string representation of the associated patient.

        Returns:
            the name of the associated patient
        """
        return '{first} {last}'.format(first=self.first_name, last=self.last_name)


class Relationship(models.Model):
    """Relationship for user and patient model."""

    patient = models.ForeignKey(
        to=Patient,
        verbose_name=_('Patient'),
        related_name='relationships',
        on_delete=models.CASCADE,
    )

    caregiver = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver'),
        related_name='relationships',
        on_delete=models.CASCADE,
    )

    default_status = RelationshipStatus.PENDING

    type = models.ForeignKey(  # noqa: A003
        to=RelationshipType,
        on_delete=models.CASCADE,
        related_name='relationship',
        verbose_name=_('Relationship Type'),
    )
    status = models.CharField(
        verbose_name=_('Relationship Status'),
        max_length=3,
        choices=RelationshipStatus.choices,
        default=default_status,
    )
    request_date = models.DateField(
        verbose_name=_('Relationship Request Date'),
    )
    start_date = models.DateField(
        verbose_name=_('Relationship Start Date'),
    )
    end_date = models.DateField(
        verbose_name=_('Relationship End Date'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Relationship')
        verbose_name_plural = _('Relationships')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_status_valid',  # noqa: WPS323
                check=models.Q(status__in=RelationshipStatus.values),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',  # noqa: WPS323
                check=models.Q(start_date__lt=models.F('end_date')),
            ),
        ]

    def __str__(self) -> str:
        """Return the relationship of the User and Patient.

        Returns:
            the relationship of the User and Patient
        """
        return '{patient} <--> {caregiver}'.format(patient=str(self.patient), caregiver=str(self.caregiver))

    def clean(self) -> None:
        """Validate if start date is earlier than end date.

        Raises:
            ValidationError: the error shows when end date is earlier than start date
        """
        if self.end_date is not None and self.start_date >= self.end_date:
            raise ValidationError({'start_date': _('Start date should be earlier than end date.')})
