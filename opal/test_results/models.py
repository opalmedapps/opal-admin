"""Module providing models for any type of test result."""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


class TestType(models.TextChoices):
    """The test type."""

    PATHOLOGY = 'P', _('Pathology')
    LAB = 'L', _('Lab')


class AbnormalFlag(models.TextChoices):
    """An enumeration of supported flags for observations."""

    LOW = 'L', _('Low')
    NORMAL = 'N', _('Normal')
    HIGH = 'H', _('High')


class AbstractObservation(models.Model):
    """An abstract representation of an observation segment within a general test report."""

    identifier_code = models.CharField(
        verbose_name=_('Observation Identifier'),
        max_length=20,
        help_text=_('Test component code.'),
    )
    identifier_text = models.CharField(
        verbose_name=_('Observation Identifier Text'),
        max_length=199,
        help_text=_('Test component text.'),
    )
    observed_at = models.DateTimeField(
        verbose_name=_('Observed At'),
        help_text=_('When this specific observation segment was entered into the source system.'),
    )
    updated_at = models.DateTimeField(
        verbose_name=_('Updated At'),
        auto_now=True,
    )

    class Meta:
        abstract = True
        ordering = ('general_test', '-updated_at')


class PathologyObservation(AbstractObservation):
    """Specific observation for Pathology tests."""

    value = models.TextField(
        verbose_name=_('Value'),
    )

    # Update the ForeignKey in this derived model
    general_test = models.ForeignKey(
        verbose_name=_('General Test'),
        to='GeneralTest',
        on_delete=models.CASCADE,
        related_name='pathology_observations',
    )

    class Meta:
        verbose_name = _('Pathology Observation')
        verbose_name_plural = _('Pathology Observations')

    def __str__(self) -> str:
        """Pathology observation string representation.

        Returns:
            string representation of the `PathologyObservation` instance
        """
        return '{code}: {observed}'.format(
            code=str(self.identifier_code),
            observed=str(self.observed_at),
        )

    def clean(self) -> None:
        """Check the validation for PathologyObservation.

        Raises:
            ValidationError: if attempting to save mismatching Observation & GeneralTest types
        """
        if self.general_test.type != TestType.PATHOLOGY:
            raise ValidationError('PathologyObservations can only be linked to GeneralTest of type PATHOLOGY.')


class LabObservation(AbstractObservation):
    """Specific observation for Lab tests."""

    value = models.FloatField(
        verbose_name=_('Value'),
    )
    value_units = models.CharField(
        verbose_name=_('Value Units'),
        max_length=20,
        blank=True,
    )
    value_min_range = models.FloatField(
        verbose_name=_('Minimum Value Range'),
        blank=True,
        null=True,
    )
    value_max_range = models.FloatField(
        verbose_name=_('Maximum Value Range'),
        blank=True,
        null=True,
    )
    value_abnormal = models.CharField(
        verbose_name=_('Abnormal Flag'),
        max_length=1,
        choices=AbnormalFlag.choices,
        default=AbnormalFlag.NORMAL,
    )

    # Update the ForeignKey in this derived model
    general_test = models.ForeignKey(
        verbose_name=_('General Test'),
        to='GeneralTest',
        on_delete=models.CASCADE,
        related_name='lab_observations',
    )

    class Meta:
        verbose_name = _('Lab Observation')
        verbose_name_plural = _('Lab Observations')

    def __str__(self) -> str:
        """Lab observation string representation.

        Returns:
            string repr
        """
        return '{code}: {value} {units} [{flag}]'.format(
            code=str(self.identifier_code),
            value=str(self.value),
            units=str(self.value_units),
            flag=str(self.value_abnormal),
        )

    def clean(self) -> None:
        """Check the validation for LabObservation.

        Raises:
            ValidationError: if attempting to save mismatching Observation & GeneralTest types
        """
        if self.general_test.type != TestType.LAB:
            raise ValidationError('LabObservations can only be linked to GeneralTest of type LAB.')


class Note(models.Model):
    """An instance of a note segment within a general test report."""

    general_test = models.ForeignKey(
        verbose_name=_('General Test'),
        to='GeneralTest',
        on_delete=models.CASCADE,
        related_name='notes',
    )
    note_source = models.CharField(
        verbose_name=_('Note Source'),
        max_length=30,
    )
    note_text = models.TextField(
        verbose_name=_('Note Text'),
    )
    updated_at = models.DateTimeField(
        verbose_name=_('Updated At'),
        auto_now=True,
    )

    class Meta:
        ordering = ('general_test', '-updated_at')
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self) -> str:
        """Return the note text attached to the parent GeneralTest representation.

        Returns:
            string repr
        """
        return '{generaltest} | {note}'.format(
            generaltest=str(self.general_test),
            note=str(self.note_text),
        )


class GeneralTest(models.Model):
    """Generalized test result instance."""

    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='general_tests',
    )
    type = models.CharField(  # noqa: A003
        verbose_name=_('Type'),
        max_length=1,
        choices=TestType.choices,
        help_text=_('The test type, for example pathlogy or regular lab.'),
    )
    sending_facility = models.CharField(
        verbose_name=_('Sending facility'),
        max_length=6,
        blank=True,
    )
    receiving_facility = models.CharField(
        verbose_name=_('Receiving facility'),
        max_length=6,
        blank=True,
    )
    collected_at = models.DateTimeField(
        verbose_name=_('Collected At'),
        help_text=_('When the specimen was collected from the patient.'),
    )
    received_at = models.DateTimeField(
        verbose_name=_('Received At'),
        help_text=_('When the test result was entered into the source system.'),
    )
    message_type = models.CharField(
        verbose_name=_('Message Type'),
        max_length=3,
        blank=True,
        help_text=_('HL7 message type indicator.'),
    )
    message_event = models.CharField(
        verbose_name=_('Message Event'),
        max_length=3,
        blank=True,
        help_text=_('HL7 message trigger event indicator.'),
    )
    test_group_code = models.CharField(
        verbose_name=_('Test Group Code'),
        max_length=30,
    )
    test_group_code_description = models.CharField(
        verbose_name=_('Test Group Code Description'),
        max_length=60,
    )
    legacy_document_id = models.IntegerField(
        verbose_name=_('Legacy Document ID'),
        blank=True,
        null=True,
        help_text=_('OpalDB.Document.DocumentSerNum, used for displaying pathology pdfs to patients.'),
    )
    case_number = models.CharField(
        verbose_name=_('Case Number'),
        help_text=_('HL7 Filler Field 1 identifier'),
        max_length=60,
        blank=True,
    )
    reported_at = models.DateTimeField(
        verbose_name=_('Reported At'),
    )

    class Meta:
        ordering = ('patient', '-collected_at')
        verbose_name = _('General Test')
        verbose_name_plural = _('General Tests')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',
                check=models.Q(type__in=TestType.values),
            ),
        ]

    def __str__(self) -> str:
        """Return the string representation of the patient, type, and specimen collection date.

        Returns:
            specimen's type and collection date associated with a patient
        """
        return '{patient} {type} Test instance [{date}]'.format(
            patient=str(self.patient),
            type=str(self.get_type_display()),
            date=str(self.collected_at),
        )

    @property
    def observations(self) -> QuerySet[PathologyObservation] | QuerySet[LabObservation]:
        """Return the correct Observation queryset depending on the type.

        Returns:
            Associated Observation model instances
        """
        if self.type == TestType.PATHOLOGY:
            return self.pathology_observations.all()

        return self.lab_observations.all()
