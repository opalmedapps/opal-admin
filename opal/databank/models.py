"""
Module providing models for the databank app.

These models serve to store metadata about the databank project, they do not
store the data itself. The data stored here includes patient consent information
and identifiers for what data has already been sent to the databank.
The actual patient data is sent to the databank via a set of API logic, after being deidentified.
"""
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from opal.legacy_questionnaires.models import LegacyAnswer
from opal.patients.models import Patient
from opal.services.data_processing.deidentification import OpenScienceIdentity, PatientData


class DatabankConsent(models.Model):
    """DatabankConsent for the donation of de-identified patient data to the research databank.

    An instance of DatabankConsent represents an Opal patient's consent preferences
    for the donation of their de-identified data to the databank. Consent preferences
    are represented by boolean fields for each 'module' of databank data.

    last_synchronized is the datetime when the Management command (on a crontab) last sent this patient's
    data to the databank.
    """

    patient = models.OneToOneField(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='databank_consent',
    )
    guid = models.CharField(
        verbose_name=_('Globally Unique Identifier'),
        max_length=64,
        unique=True,
    )
    has_appointments = models.BooleanField(
        verbose_name=_('Checked-In Appointments Consent'),
        default=True,
    )
    has_diagnoses = models.BooleanField(
        verbose_name=_('Diagnoses Consent'),
        default=True,
    )
    has_demographics = models.BooleanField(
        verbose_name=_('Demographics Consent'),
        default=True,
    )
    has_labs = models.BooleanField(
        verbose_name=_('Labs Consent'),
        default=True,
    )
    has_questionnaires = models.BooleanField(
        verbose_name=_('Questionnaires Consent'),
        default=True,
    )
    consent_granted = models.DateTimeField(
        verbose_name=_('Consent Granted'),
        auto_now_add=True,
    )
    consent_updated = models.DateTimeField(
        verbose_name=_('Consent Updated'),
        default=timezone.now,
    )
    last_synchronized = models.DateTimeField(
        verbose_name=_('Last Synchronized'),
        default=timezone.make_aware(datetime.datetime(1970, 1, 1)),
    )

    class Meta:
        verbose_name = _('Databank Consent')
        verbose_name_plural = _('Databank Consents')

    def __str__(self) -> str:
        """Return the patient's databank consents.

        Example: Patient Bart consents to donate their appointments, labs, and questionnaires data:
        str(DatabankConsent) == 'Bart Simpson : appointments, labs, questionnaires'

        Returns:
            The patient's consent information.
        """
        return "{patient}'s Databank Consent".format(
            patient=str(self.patient),
        )

    def clean(self) -> None:
        """Ensure GUID is set, or notify of missing data errors.

        Raises:
            ValidationError: If patient does not have a legacy id
        """
        if not self.patient.legacy_id:
            raise ValidationError(
                {
                    'patient__legacy_id': _("Can't generate a GUID for a patient who is missing their legacy_id."),
                },
            )
        if not self.guid or self.guid == '':
            # Retrieve this patient's middle name and city of birth responses from questionnairedb.
            results = LegacyAnswer.objects.get_guid_fields(self.patient.legacy_id)
            middle_name_cleaned = self._clean_and_validate_guid_middle_name(results)
            city_of_birth_cleaned = self._clean_and_validate_guid_city_of_birth(results)
            osi_identifiers = PatientData(
                first_name=self.patient.first_name,
                middle_name=middle_name_cleaned,
                last_name=self.patient.last_name,
                gender=self.patient.get_sex_display(),
                date_of_birth=str(self.patient.date_of_birth),
                city_of_birth=city_of_birth_cleaned,
            )
            self.guid = OpenScienceIdentity(osi_identifiers).to_signature()

    def _clean_and_validate_guid_middle_name(self, result_set: models.QuerySet) -> str:
        """Clean the middle name property, or raise error if question is missing.

        Args:
            result_set: from LegacyAnswer model manager

        Raises:
            ValidationError: only if the Middle name question is missing from the questionnaire

        Returns:
            Lowercase, space removed middle name from result set
        """
        middle_name_response = result_set.filter(question_text__icontains='middle name').first()
        if middle_name_response:
            middle_name_cleaned = middle_name_response['answer_text'].lower().replace(' ', '')
        else:
            raise ValidationError('Middle name question missing from LegacyQuestionnaireDB.')
        return str(middle_name_cleaned)

    def _clean_and_validate_guid_city_of_birth(self, result_set: models.QuerySet) -> str:
        """Clean the city of birth property, or raise error if question/response is missing.

        Args:
            result_set: from LegacyAnswer model manager

        Raises:
            ValidationError: If the city of birth question or required response is missing

        Returns:
            Lowercase, space removed city of birth from result set
        """
        city_of_birth_response = result_set.filter(question_text__icontains='city of birth').first()
        if city_of_birth_response:
            city_of_birth_cleaned = city_of_birth_response['answer_text'].lower().replace(' ', '')
        else:
            raise ValidationError('City of birth question or response missing from LegacyQuestionnaireDB.')
        return str(city_of_birth_cleaned)


class DataModuleType(models.TextChoices):
    """An enumeration of supported data modules for the databank."""

    APPOINTMENTS = 'APPT', _('Appointments')
    DIAGNOSES = 'DIAG', _('Diagnoses')
    DEMOGRAPHICS = 'DEMO', _('Demographics')
    LABS = 'LABS', _('Labs')
    QUESTIONNAIRES = 'QSTN', _('Questionnaires')


class SharedData(models.Model):
    """A piece of data sent to the databank.

    Each instance contains some identifiers for each piece of data sent to the databank.
    """

    databank_consent = models.ForeignKey(
        verbose_name=_('Databank Consent'),
        to=DatabankConsent,
        on_delete=models.CASCADE,
        related_name='shared_data',
    )
    sent_at = models.DateTimeField(
        verbose_name=_('Sent At'),
        auto_now=True,
    )
    data_id = models.IntegerField(verbose_name=_('Data ID'))
    data_type = models.CharField(
        verbose_name=_('Data Type'),
        max_length=4,
        choices=DataModuleType.choices,
    )

    class Meta:
        verbose_name = _('Shared Datum')
        verbose_name_plural = _('Shared Data')
        ordering = ('-sent_at',)
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_data_type_valid',
                check=models.Q(data_type__in=DataModuleType.values),
            ),
        ]
        # TODO: After finalizing retrieval queries, add indexes to SharedData to reduce query time.
        #       Indexing will depend on what we will be searching by (databank_consent+data_type?)

    def __str__(self) -> str:
        """
        Return the type and sent date of this datum instance.

        Returns:
            the textual representation of this instance
        """
        return f'{self.get_data_type_display()} datum, sent at {self.sent_at}'
