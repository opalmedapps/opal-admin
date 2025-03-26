"""
Module providing models for the databank app.

These models serve to store metadata about the databank project, they do not
store the data itself. The data stored here includes patient consent information
and identifiers for what data has already been sent to the databank.
The actual patient data is sent to the databank via a set of API logic, after being deidentified.
"""
import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


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
        # Filtering or sorting this table by sent_at, databank_consent, or both together will be faster
        indexes = [
            models.Index(fields=['sent_at'], name='sent_at_idx'),
            models.Index(fields=['databank_consent', 'sent_at'], name='databank_consent_sent_at_idx'),
        ]

    def __str__(self) -> str:
        """
        Return the type and sent date of this datum instance.

        Returns:
            the textual representation of this instance
        """
        return f'{self.get_data_type_display()} datum, sent at {self.sent_at}'
