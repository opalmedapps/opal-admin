"""Module providing models for the patients app."""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.caregivers.models import CaregiverProfile
from opal.core.validators import validate_ramq
from opal.hospital_settings.models import Site
from opal.patients.managers import HospitalPatientManager, RelationshipManager

from . import constants


class RelationshipType(models.Model):
    """A type of relationship between a user (aka caregiver) and patient."""

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=25,
        unique=True,
    )
    description = models.CharField(
        verbose_name=_('Description'),
        max_length=200,
    )
    start_age = models.PositiveIntegerField(
        verbose_name=_('Start age'),
        help_text=_('Minimum age the relationship is allowed to start.'),
        validators=[
            MinValueValidator(constants.RELATIONSHIP_MIN_AGE),
            MaxValueValidator(constants.RELATIONSHIP_MAX_AGE - 1),
        ])
    end_age = models.PositiveIntegerField(
        verbose_name=_('End age'),
        help_text=_('Age at which the relationship ends automatically.'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(constants.RELATIONSHIP_MIN_AGE + 1),
            MaxValueValidator(constants.RELATIONSHIP_MAX_AGE),
        ])
    form_required = models.BooleanField(
        verbose_name=_('Form required'),
        default=True,
        help_text=_('Whether the hospital form is required to be completed by the caregiver'),
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Caregiver Relationship Type')
        verbose_name_plural = _('Caregiver Relationship Types')

    def __str__(self) -> str:
        """Return the string representation of the User Patient Relationship Type.

        Returns:
            the name of the user patient relationship type
        """
        return self.name


class SexType(models.TextChoices):
    """
    The choice of sex types.

    The available types are currently defined as they are used at the MUHC.
    The values are the raw values as they are retrieved in HL7.
    """

    FEMALE = 'F', _('Female')
    MALE = 'M', _('Male')
    OTHER = 'O', _('Other')
    UNKNOWN = 'U', _('Unknown')


class Patient(models.Model):
    """A patient whose data can be accessed."""

    # TextChoices need to be defined outside to use them in constraints
    # define them as class attributes for easier access
    # see: https://stackoverflow.com/q/71522816
    SexType = SexType

    first_name = models.CharField(
        verbose_name=_('First Name'),
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name=_('Last Name'),
        max_length=150,
    )
    date_of_birth = models.DateField(
        verbose_name=_('Date of Birth'),
    )
    date_of_death = models.DateTimeField(
        verbose_name=_('Date and Time of Death'),
        null=True,
        blank=True,
    )
    sex = models.CharField(
        verbose_name=_('Sex'),
        max_length=1,
        choices=SexType.choices,
    )
    ramq = models.CharField(
        verbose_name=_('RAMQ Number'),
        max_length=12,
        validators=[
            MinLengthValidator(12),
            validate_ramq,
        ],
        unique=True,
        blank=True,
        null=True,
    )
    caregivers = models.ManyToManyField(
        verbose_name=_('Caregivers'),
        related_name='patients',
        to=CaregiverProfile,
        through='Relationship',
    )
    legacy_id = models.PositiveIntegerField(
        verbose_name=_('Legacy ID'),
        validators=[MinValueValidator(1)],
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_sex_valid',  # noqa: WPS323
                check=models.Q(sex__in=SexType.values),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',  # noqa: WPS323
                check=models.Q(date_of_birth__lte=models.F('date_of_death')),
            ),
        ]

    def __str__(self) -> str:
        """
        Return the string representation of the associated patient.

        Returns:
            the name of the associated patient
        """
        return '{first} {last}'.format(first=self.first_name, last=self.last_name)

    def clean(self) -> None:
        """Validate date fields.

        Raises:
            ValidationError: If the date of death is earlier than the date of birth.
        """
        if self.date_of_death is not None and self.date_of_birth > self.date_of_death.date():
            raise ValidationError({'date_of_death': _('Date of death cannot be earlier than date of birth.')})


class RelationshipStatus(models.TextChoices):
    """Choice of relationship status."""

    PENDING = 'PEN', _('Pending')
    CONFIRMED = 'CON', _('Confirmed')
    DENIED = 'DEN', _('Denied')
    EXPIRED = 'EXP', _('Expired')
    REVOKED = 'REV', _('Revoked')


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
        default=RelationshipStatus.PENDING,
    )

    reason = models.CharField(
        verbose_name=_('Reason of Status Change'),
        max_length=255,
        blank=True,
        default=None,
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
    objects: RelationshipManager = RelationshipManager()

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
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_constraint',  # noqa: WPS323
                fields=['patient', 'caregiver', 'type', 'status'],
            ),
        ]

    def __str__(self) -> str:
        """Return the relationship of the User and Patient.

        Returns:
            the relationship of the User and Patient
        """
        return '{patient} <--> {caregiver} [{type}]'.format(
            patient=str(self.patient),
            caregiver=str(self.caregiver),
            type=str(self.type),
        )

    def clean(self) -> None:
        """Validate date and reason fields.

        Raises:
            ValidationError: the error shows when enteries do not comply with the validation rules.
        """
        if self.end_date is not None and self.start_date >= self.end_date:
            raise ValidationError({'start_date': _('Start date should be earlier than end date.')})
        # validate status is not empty if status is revoked or denied.
        if not self.reason:
            if self.status in RelationshipStatus.REVOKED or self.status in RelationshipStatus.DENIED:
                raise ValidationError({'reason': _('Reason is mandatory when status is denied or revoked.')})


class HospitalPatient(models.Model):
    """Hospital Patient model."""

    patient = models.ForeignKey(
        to=Patient,
        verbose_name=_('Patient'),
        related_name='hospital_patients',
        on_delete=models.CASCADE,
    )
    site = models.ForeignKey(
        to=Site,
        verbose_name=_('Site'),
        related_name='hospital_patients',
        on_delete=models.CASCADE,
    )
    mrn = models.CharField(
        verbose_name=_('Medical Record Number'),
        max_length=10,
    )
    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
    )
    objects: HospitalPatientManager = HospitalPatientManager()

    class Meta:
        verbose_name = _('Hospital Patient')
        verbose_name_plural = _('Hospital Patients')
        unique_together = (('site', 'mrn'),)

    def __str__(self) -> str:
        """Return the Patient Hospital Identifier of the Patient.

        Returns:
            the Patient Hospital Identifier of the Patient
        """
        return '{patient} ({site_code}: {mrn})'.format(
            patient=str(self.patient),
            site_code=str(self.site.code),
            mrn=str(self.mrn),
        )
