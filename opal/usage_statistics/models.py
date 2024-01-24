"""Prototype models for usage statistics."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient, Relationship, SexType
from opal.users.models import User

Language = settings.LANGUAGES


class DailyUserAppActivity(models.Model):
    """Tracks daily app activity per user and patient. One record per user + patient per day (Maximum)."""

    action_by_user = models.ForeignKey(
        verbose_name=_('User who triggered this action'),
        to=User,
        on_delete=models.CASCADE,
    )
    user_relationship_to_patient = models.ForeignKey(
        verbose_name=_('Relationship between user and patient'),
        to=Relationship,
        on_delete=models.CASCADE,
        null=True,
    )
    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        null=True,
    )
    last_login = models.DateTimeField(
        verbose_name=_('Last Login'),
        null=True,
    )
    count_logins = models.PositiveIntegerField(
        verbose_name=_('Count Logins'),
        validators=[MinValueValidator(0)],
    )
    count_checkins = models.PositiveIntegerField(
        verbose_name=_('Count Checkins'),
        validators=[MinValueValidator(0)],
    )
    count_documents = models.PositiveIntegerField(
        verbose_name=_('Count Documents'),
        validators=[MinValueValidator(0)],
    )
    count_educational_materials = models.PositiveIntegerField(
        verbose_name=_('Count Educational Materials'),
        validators=[MinValueValidator(0)],
    )
    count_feedback = models.PositiveIntegerField(
        verbose_name=_('Count Feedbacks'),
        validators=[MinValueValidator(0)],
    )
    count_questionnaires_complete = models.PositiveIntegerField(
        verbose_name=_('Count Questionnaires'),
        validators=[MinValueValidator(0)],
    )
    count_labs = models.PositiveIntegerField(
        verbose_name=_('Count Labs'),
        validators=[MinValueValidator(0)],
    )
    count_update_security_answers = models.PositiveIntegerField(
        verbose_name=_('Count Security Answer Updates'),
        validators=[MinValueValidator(0)],
    )
    count_update_passwords = models.PositiveIntegerField(
        verbose_name=_('Count Password Updates'),
        validators=[MinValueValidator(0)],
    )
    count_update_language = models.PositiveIntegerField(
        verbose_name=_('Count Language Updates'),
        validators=[MinValueValidator(0)],
    )
    count_device_ios = models.PositiveIntegerField(
        verbose_name=_('IOS Devices'),
        validators=[MinValueValidator(0)],
    )
    count_device_android = models.PositiveIntegerField(
        verbose_name=_('Android Devices'),
        validators=[MinValueValidator(0)],
    )
    count_device_browser = models.PositiveIntegerField(
        verbose_name=_('Browser Devices'),
        validators=[MinValueValidator(0)],
    )
    date_added = models.DateField(
        verbose_name=_('Date Added'),
        default=timezone.now,
    )

    class Meta:
        verbose_name = _('User App Activity')
        verbose_name_plural = _('User App Activities')

    def __str__(self) -> str:
        """
        Return a string representation of the activity, including user and patient details.

        If self.patient is null, then this activity was an account activity not occuring in a patient chart.

        Returns:
            String representing the activity.
        """
        # TODO: Change the string to 'Daily activity by user XX in the chart of patient YY?' That might be more descriptive?  # noqa: E501
        if self.patient:
            return f'Daily activity by {self.action_by_user.first_name}, {self.action_by_user.last_name} for Patient {self.patient}'  # noqa: WPS221, E501
        return f'Daily activity by {self.action_by_user.first_name}, {self.action_by_user.last_name}'


class DailyPatientDataReceived(models.Model):
    """Tracks daily data sent to patient. One record per patient per day (Maximum)."""

    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
    )
    next_appointment = models.DateTimeField(
        verbose_name=_('Next Appointment'),
        null=True,
        blank=False,
    )
    last_appointment_received = models.DateTimeField(
        verbose_name=_('Last Appointment Received'),
        null=True,
        blank=False,
    )
    appointments_received = models.PositiveIntegerField(
        verbose_name=_('Appointments Received'),
        validators=[MinValueValidator(0)],
    )
    last_document_received = models.DateTimeField(
        verbose_name=_('Last Document Received'),
        null=True,
        blank=False,
    )
    documents_received = models.PositiveIntegerField(
        verbose_name=_('Documents Received'),
        validators=[MinValueValidator(0)],
    )
    last_educational_materials_received = models.DateTimeField(
        verbose_name=_('Last Educational Materials Received'),
        null=True,
        blank=False,
    )
    educational_materials_received = models.PositiveIntegerField(
        verbose_name=_('Educational Materials Received'),
        validators=[MinValueValidator(0)],
    )
    last_questionnaire_received = models.DateTimeField(
        verbose_name=_('Last Questionnaire Received'),
        null=True,
        blank=False,
    )
    questionnaires_received = models.PositiveIntegerField(
        verbose_name=_('Questionnaires Received'),
        validators=[MinValueValidator(0)],
    )
    last_lab_received = models.DateTimeField(
        verbose_name=_('Last Lab Received'),
        null=True,
        blank=False,
    )
    labs_received = models.PositiveIntegerField(
        verbose_name=_('Labs Received'),
        validators=[MinValueValidator(0)],
    )
    date_added = models.DateTimeField(
        verbose_name=_('Date Added'),
        default=timezone.now,
    )

    class Meta:
        verbose_name = _('Patient Data Received')
        verbose_name_plural = _('Patient Data Received Records')

    def __str__(self) -> str:
        """
        Return a string representation of the data received for a patient.

        Returns:
            String representing the patient data received.
        """
        return f'{self.patient} received data on {self.date_added.date()}'


class PatientDemographic(models.Model):
    """Tracks daily demographic statistics. One record per patient per day.

    This communicates a 'snapshot' of a patients demographic information every day.
    """

    patient = models.ForeignKey(
        verbose_name=_('Subject Patient'),
        to=Patient,
        on_delete=models.CASCADE,
    )
    sex = models.CharField(
        verbose_name=_('Sex'),
        max_length=1,
        choices=SexType.choices,
    )
    language = models.CharField(
        verbose_name=_('Language'),
        max_length=2,
        choices=Language,
        # use the language code of the first language
        default=Language[0][0],
    )
    access_level = models.IntegerField(verbose_name=_('Access Level'))
    blocked_status = models.BinaryField(verbose_name=_('Blocked Status'))
    status_reason = models.CharField(
        verbose_name=_('Status Reason'),
        max_length=256,
    )
    completed_registration = models.CharField(
        verbose_name=_('Completed Registration'),
        max_length=3,
    )
    date_added = models.DateTimeField(
        verbose_name=_('Date Added'),
        default=timezone.now,
    )

    class Meta:
        verbose_name = _('Patient Demographic')
        verbose_name_plural = _('Patient Demographics')

    def __str__(self) -> str:
        """
        Return a string representation of the daily demographic statistics for a patient.

        Returns:
            String representing the patient's daily demographics.
        """
        return f'{self.patient} demographic snapshot at {self.date_added}'
