# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing models for the patients app."""

from collections import defaultdict
from datetime import date
from typing import Any, Final
from uuid import uuid4

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from dateutil.relativedelta import relativedelta

from opal.caregivers.models import CaregiverProfile
from opal.core.models import AbstractLabDelayModel
from opal.core.validators import validate_ramq
from opal.hospital_settings.models import Institution, Site
from opal.patients.managers import PatientManager, PatientQueryset, RelationshipManager, RelationshipTypeManager

from . import constants


class RoleType(models.TextChoices):
    """Choices for role type within the [opal.patients.models.RelationshipType][] model."""

    # 'self' is a reserved keyword in Python requiring a noqa here.
    SELF = 'SELF', _('Self')
    PARENT_GUARDIAN = 'PARENTGUARDIAN', _('Parent/Guardian')
    GUARDIAN_CAREGIVER = 'GRDNCAREGIVER', _('Guardian-Caregiver')
    MANDATARY = 'MANDATARY', _('Mandatary')
    CAREGIVER = 'CAREGIVER', _('Caregiver')


# defined here instead of constants to avoid circular import
#: Set of role types for which a relationship type is predefined via a data migration
PREDEFINED_ROLE_TYPES: Final[set[RoleType]] = {
    RoleType.SELF,
    RoleType.PARENT_GUARDIAN,
    RoleType.GUARDIAN_CAREGIVER,
    RoleType.MANDATARY,
}


class RelationshipType(models.Model):
    """A type of relationship between a user (aka caregiver) and patient."""

    # TextChoices need to be defined outside to use them in constraints
    # define them as class attributes for easier access
    # see: https://stackoverflow.com/q/71522816
    RoleType = RoleType

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
        verbose_name=_('Can answer patient questionnaires'),
        default=False,
        help_text=_('The caregiver can answer questionnaires on behalf of the patient.'),
    )
    role_type = models.CharField(
        verbose_name=_('Role Type'),
        choices=RoleType.choices,  # type: ignore[misc]
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
        verbose_name = _('Relationship Type')
        verbose_name_plural = _('Relationship Types')

    def __str__(self) -> str:
        """
        Return the string representation of the User Patient Relationship Type.

        Returns:
            the name of the user patient relationship type
        """
        return self.name

    def clean(self) -> None:
        """
        Validate the model being saved does not add an extra pre-defined role type.

        If additional predefined role types are added in the future,
        add them to the predefined RoleType lists here.

        Raises:
            ValidationError: If the changes result in a missing or extra restricted role type.
        """
        # Verify we cannot add an additional predefined type
        # AND that the current instance being checked isn't already in the existing restricted list
        # (which would mean this is an 'update' operation, and should not raise an exception)
        role_type = self.role_type

        if role_type in PREDEFINED_ROLE_TYPES:
            existing_predefined_relationship_type = RelationshipType.objects.get(
                role_type=self.role_type,
            )

            if self != existing_predefined_relationship_type:
                raise ValidationError({
                    'role_type': _('There already exists a relationship type with this role type'),
                })

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """
        Delete the instance.

        Prevents deletion of instances that have a `role_type` other than _Caregiver_.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Raises:
            ValidationError: if the instance does not have a `role_type` of _Caregiver_

        Returns:
            Number of models deleted and dict of models deleted.
        """
        if self.role_type != RoleType.CAREGIVER:
            raise ValidationError(
                _('The relationship type with this role type cannot be deleted'),
            )

        return super().delete(*args, **kwargs)

    @property
    def is_self(self) -> bool:
        """
        Check whether the RelationshipType is a "Self" role type.

        Returns:
            True if the role type is SELF.
        """
        return self.role_type == RoleType.SELF


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


class DataAccessType(models.TextChoices):
    """The desired access level for the patient's data."""

    ALL = 'ALL', _('All')
    NEED_TO_KNOW = 'NTK', _('Need To Know')


class Patient(AbstractLabDelayModel):
    """A patient whose data can be accessed."""

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
        blank=True,
    )
    data_access = models.CharField(
        verbose_name=_('Data Access Level'),
        max_length=3,
        choices=DataAccessType.choices,
        default=DataAccessType.ALL,
    )
    caregivers: models.ManyToManyField[CaregiverProfile, 'Relationship'] = models.ManyToManyField(
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
    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        default=timezone.now,
    )

    objects = PatientManager.from_queryset(PatientQueryset)()

    class Meta:
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_sex_valid',
                check=models.Q(sex__in=SexType.values),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',
                check=models.Q(date_of_birth__lte=models.F('date_of_death')),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_access_level_valid',
                check=models.Q(data_access__in=DataAccessType.values),
            ),
        ]

    def __str__(self) -> str:
        """
        Return the string representation of the associated patient.

        Returns:
            the name of the associated patient
        """
        return f'{self.last_name}, {self.first_name}'

    def clean(self) -> None:
        """
        Validate date fields.

        Raises:
            ValidationError: If the date of death is earlier than the date of birth.
        """
        if self.date_of_death is not None and self.date_of_birth > self.date_of_death.date():
            raise ValidationError({'date_of_death': _('Date of death cannot be earlier than date of birth.')})

    @property
    def health_insurance_number(self) -> str:
        """Return the health insurance number of the patient."""
        return self.ramq

    @property
    def age(self) -> int:
        """
        Return the age of the patient.

        Returns:
            the age of the patient
        """
        return Patient.calculate_age(self.date_of_birth)

    @property
    def is_adult(self) -> bool:
        """
        Return whether the patient is an adult.

        Returns:
            True, if the patient's age is greater equal than the institution's adulthood age, False otherwise
        """
        return self.age >= Institution.objects.get().adulthood_age

    @classmethod
    def calculate_age(cls, date_of_birth: date, reference_date: date | None = None) -> int:
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
            reference_date = timezone.now().date()
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

    type = models.ForeignKey(
        to=RelationshipType,
        on_delete=models.CASCADE,
        related_name='relationship',
        verbose_name=_('Relationship Type'),
    )

    status = models.CharField(
        verbose_name=_('Status'),
        max_length=3,
        choices=RelationshipStatus.choices,
        default=RelationshipStatus.PENDING,
    )

    reason = models.CharField(
        verbose_name=_('Reason of Status Change'),
        max_length=255,
        blank=True,
        default='',
    )

    request_date = models.DateField(
        verbose_name=_('Request Date'),
    )

    start_date = models.DateField(
        verbose_name=_('Start Date'),
    )

    end_date = models.DateField(
        verbose_name=_('End Date'),
        null=True,
        blank=True,
    )
    objects: RelationshipManager = RelationshipManager()

    class Meta:
        permissions = (
            ('can_manage_relationships', _('Can manage relationships')),
            ('can_perform_registration', _('Can perform registration')),
        )
        verbose_name = _('Relationship')
        verbose_name_plural = _('Relationships')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_status_valid',
                check=models.Q(status__in=RelationshipStatus.values),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',
                check=models.Q(start_date__lt=models.F('end_date')),
            ),
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_constraint',
                fields=['patient', 'caregiver', 'type', 'status'],
            ),
        ]

    def __str__(self) -> str:
        """
        Return the relationship of the User and Patient.

        Returns:
            the relationship of the User and Patient
        """
        return f'{self.patient} <--> {self.caregiver} [{self.type}]'

    def validate_start_date(self) -> list[str]:
        """
        Validate the `start_date` field.

        The start date has to be greater equals the patient's date of birth.
        The start date has to be earlier than the end date.

        Returns:
            a list of error messages
        """
        errors = []

        if self.start_date < self.patient.date_of_birth:
            errors.append(gettext("Start date cannot be earlier than patient's date of birth."))

        if self.end_date is not None and self.start_date >= self.end_date:
            errors.append(gettext('Start date should be earlier than end date.'))

        return errors

    def validate_end_date(self) -> list[str]:
        """
        Validate the `end_date` field.

        The end date has to be earlier than the date when the patient turns to older age period.

        Returns:
            a list of error messages
        """
        errors = []

        # calculate the end date based on patient's birthday and relationship type
        end_date = self.calculate_end_date(self.patient.date_of_birth, self.type)
        if self.end_date is not None and end_date is not None and self.end_date > end_date:
            errors.append(
                gettext(
                    'End date for {relationship_type} relationship cannot be later than {end_date}.',
                ).format(
                    relationship_type=self.type,
                    end_date=end_date,
                )
            )

        if self.end_date is not None and self.end_date <= self.start_date:
            errors.append(gettext('End date should be later than start date.'))

        return errors

    def validate_type(self) -> list[str]:
        """
        Validate the `type` field.

        Returns:
            a list of error messages
        """
        errors = []

        if (
            hasattr(self, 'patient')
            and self.type.role_type == RoleType.SELF
            # exclude the current instance to support updating it
            and Relationship.objects.exclude(
                pk=self.pk,
            )
            .filter(
                patient=self.patient,
                type__role_type=RoleType.SELF,
            )
            .exists()
        ):
            errors.append(gettext('The patient already has a self-relationship.'))

        if (
            hasattr(self, 'caregiver')
            and self.type.role_type == RoleType.SELF
            # exclude the current instance to support updating it
            and Relationship.objects.exclude(
                pk=self.pk,
            )
            .filter(
                caregiver=self.caregiver,
                type__role_type=RoleType.SELF,
            )
            .exists()
        ):
            errors.append(gettext('The caregiver already has a self-relationship.'))

        return errors

    def clean(self) -> None:
        """
        Validate additionally across fields.

        Raises:
            ValidationError: the error shows when entries do not comply with the validation rules.
        """
        # support adding multiple errors for the same field/non-fields
        errors: dict[str, list[str]] = defaultdict(list)

        if self.start_date is not None and hasattr(self, 'patient'):  # type: ignore[redundant-expr]
            start_date_errors = self.validate_start_date()

            if start_date_errors:
                errors['start_date'].extend(start_date_errors)

            end_date_errors = self.validate_end_date()

            if end_date_errors:
                errors['end_date'].extend(end_date_errors)

        # validate status is not empty if status is revoked or denied.
        if not self.reason and self.status in {RelationshipStatus.REVOKED, RelationshipStatus.DENIED}:
            errors['reason'].append(gettext('Reason is mandatory when status is denied or revoked.'))

        if hasattr(self, 'type'):
            if self.type.role_type == RoleType.SELF and self.status == RelationshipStatus.PENDING:
                errors['status'].append(gettext('"Pending" status does not apply for the Self relationship.'))

            type_errors = self.validate_type()

            if type_errors:
                errors[NON_FIELD_ERRORS].extend(type_errors)

        if (
            hasattr(self, 'patient')
            and hasattr(self, 'caregiver')
            # exclude the current instance to support updating it
            and Relationship.objects.exclude(
                pk=self.pk,
            )
            .filter(
                patient=self.patient,
                caregiver=self.caregiver,
                status__in={RelationshipStatus.CONFIRMED, RelationshipStatus.PENDING},
            )
            .exists()
        ):
            errors[NON_FIELD_ERRORS].append(
                gettext('There already exists an active relationship between the patient and caregiver.'),
            )

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
                RelationshipStatus.REVOKED,
            ]
        elif current == RelationshipStatus.DENIED:
            statuses += [RelationshipStatus.CONFIRMED, RelationshipStatus.PENDING]
        elif current == RelationshipStatus.REVOKED:
            statuses += [RelationshipStatus.CONFIRMED]

        return statuses

    @classmethod
    def calculate_default_start_date(
        cls,
        request_date: date,
        date_of_birth: date,
        relationship_type: RelationshipType,
    ) -> date:
        """
        Calculate the start date for the relationship between a patient and a caregiver.

        Args:
            request_date: the date when the requestor submit the access request
            date_of_birth: patient's date of birth
            relationship_type: the type of relationship between the caregiver and the patient

        Returns:
            the start date
        """
        return request_date if relationship_type.role_type == RoleType.MANDATARY else date_of_birth

    @classmethod
    def calculate_end_date(cls, date_of_birth: date, relationship_type: RelationshipType) -> date | None:
        """
        Calculate the end date for the relationship between a patient and a caregiver.

        If the relationship type has an end age,
        the end date is restricted to the date where the patient turns that age.

        Args:
            date_of_birth: patient's date of birth
            relationship_type: the type of relationship between the caregiver and the patient

        Returns:
            the end date
        """
        reference_date = None

        if relationship_type.end_age:
            # Calculate the date at which the patient turns to the end age of relationship type
            reference_date = date_of_birth + relativedelta(years=relationship_type.end_age)
        return reference_date

    @classmethod
    def max_end_date(cls, date_of_birth: date) -> date:
        """
        Get the max end date for the relationship between a patient and a caregiver.

        The max end date equals to start date plus RELATIONSHIP_MAX_AGE.

        Args:
            date_of_birth: patient's date of birth

        Returns:
            the max end date
        """
        return date_of_birth + relativedelta(years=constants.RELATIONSHIP_MAX_AGE)


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
        """
        Return the textual representation of this instance.

        Returns:
            the textual representation of this instance
        """
        return f'{self.site.acronym}: {self.mrn}'
