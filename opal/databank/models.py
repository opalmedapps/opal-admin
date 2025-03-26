"""
Module providing models for the databank app.

These models serve to store metadata about the databank project, they do not
store the data itself. The data stored here includes patient consent information
and identifiers for what data has already been sent to the databank.
The actual patient data is sent to the databank via a set of API logic, after being deidentified.
"""
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
    # TODO: Add `databank_id` field after determining hash algo with LORIS team
    has_appointments = models.BooleanField(
        verbose_name=_('Checked-In Appointments Consent'),
        default=True,
    )
    has_diagnosis = models.BooleanField(
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
