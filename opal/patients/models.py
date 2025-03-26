"""Module providing models for the patients app."""
from collections import defaultdict
from datetime import date
from typing import Any, Optional, TypeAlias
from uuid import uuid4

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from opal.caregivers.models import CaregiverProfile
from opal.core.validators import validate_ramq
from opal.hospital_settings.models import Site
from opal.patients.managers import PatientManager, PatientQueryset, RelationshipManager, RelationshipTypeManager

from . import constants


class RoleType(models.TextChoices):
    """Choices for role type within the [opal.patients.models.RelationshipType][] model."""

    # 'self' is a reserved keyword in Python requiring a noqa here.
    SELF = 'SELF', _('Self')  # noqa: WPS117
    CAREGIVER = 'CAREGIVER', _('Caregiver')
    PARENT_GUARDIAN = 'PARENTGUARDIAN', _('Parent/Guardian')


class RelationshipType(models.Model):
    """A type of relationship between a user (aka caregiver) and patient."""

    # TextChoices need to be defined outside to use them in constraints
    # define them as class attributes for easier access
    # see: https://stackoverflow.com/q/71522816
    RoleType: TypeAlias = RoleType

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
        ],
    )
    end_age = models.PositiveIntegerField(
        verbose_name=_('End age'),
        help_text=_('Age at which the relationship ends automatically.'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(constants.RELATIONSHIP_MIN_AGE + 1),
            MaxValueValidator(constants.RELATIONSHIP_MAX_AGE),
        ],
    )
    form_required = models.BooleanField(
        verbose_name=_('Form required'),
        default=True,
        help_text=_('Whether the hospital form is required to be completed by the caregiver'),
    )
    can_answer_questionnaire = models.BooleanField(
        verbose_name=_('Right to answer questionnaire'),
        default=False,
        help_text=_('The caregiver can answer questionnaires on behalf of the patient.'),
    )
    role_type = models.CharField(
        verbose_name=_('Relationship Role Type'),
        choices=RoleType.choices,
        default=RoleType.CAREGIVER,
        max_length=14,
        help_text=_(
            'Role types track the category of relationship between a caregiver and patient.'
            + ' A "Self" role type indicates a patient who owns the data that is being accessed.',
        ),
    )

    objects = RelationshipTypeManager()  # type: ignore[django-manager-missing]

    class Meta:
        permissions = (('can_manage_relationshiptypes', _('Can manage relationship types')),)
        ordering = ['name']
        verbose_name = _('Caregiver Relationship Type')
        verbose_name_plural = _('Caregiver Relationship Types')

    def __str__(self) -> str:
        """Return the string representation of the User Patient Relationship Type.

        Returns:
            the name of the user patient relationship type
        """
        return self.name

    def clean(self) -> None:
        """Validate the model being saved does not add an extra SELF or PARENT_GUARDIAN role type.

        If additional restricted role types are added in the future, add them to the RoleType lists here.

        Raises:
            ValidationError: If the changes result in a missing or extra restricted roletype.
        """
        existing_restricted_relationshiptypes = RelationshipType.objects.filter(
            role_type__in=[RoleType.SELF, RoleType.PARENT_GUARDIAN],
        )
        existing_restricted_roletypes = [rel.role_type for rel in existing_restricted_relationshiptypes]

        # Verify we cannot add an additional self or parent role type
        # AND that the current instance being checked isnt already in the existing restricted list
        # (which would mean this is an 'update' operation, and should not raise an exception)
        if (
            self.role_type == RoleType.SELF
            and RoleType.SELF in existing_restricted_roletypes
            and self not in existing_restricted_relationshiptypes
        ):
            raise ValidationError(
                _('There must always be exactly one Self and one Parent/Guardian role'),
            )

        if (
            self.role_type == RoleType.PARENT_GUARDIAN
            and RoleType.PARENT_GUARDIAN in existing_restricted_roletypes
            and self not in existing_restricted_relationshiptypes
        ):
            raise ValidationError(
                _('There must always be exactly one Self and one Parent/Guardian role'),
            )

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Validate the model being deleted is not of type 'self'.

        Args:
            args: Any number of arguments.
            kwargs: Any number of key word arguments.

        Raises:
            ValidationError: If a new relationship is being created/edited with role_type self and one already exists.

        Returns:
            Number of models deleted and dict of models deleted.
        """
        if self.role_type in {RoleType.SELF, RoleType.PARENT_GUARDIAN}:
            raise ValidationError(
                _('The relationship type with this role type cannot be deleted'),
            )
        return super().delete(*args, **kwargs)


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
    SexType: TypeAlias = SexType

    uuid = models.UUIDField(
        verbose_name=_('UUID'),
        unique=True,
        default=uuid4,
        editable=False,
    )

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
    objects = PatientManager.from_queryset(PatientQueryset)()

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

    @classmethod
    def calculate_age(cls, date_of_birth: date, reference_date: Optional[date] = None) -> int:
        """
        Return the age based on the given date of birth.

        Args:
            date_of_birth: patient's date of birth
            reference_date: a given date and default value is today

        Returns:
            the age based on the given date of birth.
        """
        # Get today's date object if reference date is None
        if reference_date is None:
            reference_date = date.today()
        # A bool that represents if reference date's day/month precedes the birth day/month
        one_or_zero = (reference_date.month, reference_date.day) < (date_of_birth.month, date_of_birth.day)
        # Calculate the difference in years from the date object's components
        year_difference = reference_date.year - date_of_birth.year
        # The difference in years is not enough.
        # To get it right, subtract 1 or 0 based on if reference date precedes the birthdate's month/day.
        return year_difference - one_or_zero


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
        permissions = (('can_manage_relationships', _('Can manage relationships')),)
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
            ValidationError: the error shows when entries do not comply with the validation rules.
        """
        # support adding multiple errors for the same field/non-fields
        errors: dict[str, list[str]] = defaultdict(list)

        if self.end_date is not None and self.start_date >= self.end_date:
            errors['start_date'].append(gettext('Start date should be earlier than end date.'))
        # validate status is not empty if status is revoked or denied.
        if not self.reason and self.status in {RelationshipStatus.REVOKED, RelationshipStatus.DENIED}:
            errors['reason'].append(gettext('Reason is mandatory when status is denied or revoked.'))

        if (
            self.type.role_type == RoleType.SELF
            and Relationship.objects.filter(patient=self.patient, type__role_type=RoleType.SELF).exists()
        ):
            errors[NON_FIELD_ERRORS].append(gettext('The patient already has a self-relationship'))

        if (
            self.type.role_type == RoleType.SELF
            and Relationship.objects.filter(caregiver=self.caregiver, type__role_type=RoleType.SELF).exists()
        ):
            errors[NON_FIELD_ERRORS].append(gettext('The caregiver already has a self-relationship'))

        if errors:
            raise ValidationError(errors)

    @classmethod
    def valid_statuses(cls, current: RelationshipStatus) -> list[RelationshipStatus]:
        """
        Return the list of statuses the provided status can be transitioned to.

        Args:
            current: the selected value of the status

        Returns:
            list of valid statuses
        """
        statuses = [current]
        if current == RelationshipStatus.PENDING:
            statuses += [RelationshipStatus.DENIED, RelationshipStatus.CONFIRMED]
        elif current == RelationshipStatus.CONFIRMED:
            statuses += [
                RelationshipStatus.PENDING,
                RelationshipStatus.DENIED,
                RelationshipStatus.REVOKED,
            ]
        elif current == RelationshipStatus.DENIED:
            statuses += [RelationshipStatus.CONFIRMED, RelationshipStatus.PENDING]
        elif current == RelationshipStatus.REVOKED:
            statuses += [RelationshipStatus.CONFIRMED]

        return statuses


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

    class Meta:
        verbose_name = _('Hospital Patient')
        verbose_name_plural = _('Hospital Patients')
        unique_together = (('site', 'mrn'), ('patient', 'site'))

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
