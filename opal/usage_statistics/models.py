# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing models for the usage statistics app."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient, Relationship
from opal.users.models import User


class DailyUserPatientActivity(models.Model):
    """
    Daily application activity by a user on behalf of a patient.

    One record per user + patient per day (Maximum).
    """

    action_by_user = models.ForeignKey(
        verbose_name=_('User who triggered this action'),
        to=User,
        on_delete=models.CASCADE,
        related_name='daily_patient_activities',
    )
    user_relationship_to_patient = models.ForeignKey(
        verbose_name=_('Relationship between user and patient'),
        to=Relationship,
        on_delete=models.CASCADE,
        related_name='daily_patient_activities',
    )
    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='daily_patient_activities',
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
    count_questionnaires_complete = models.PositiveIntegerField(
        verbose_name=_('Count Questionnaires'),
        validators=[MinValueValidator(0)],
    )
    count_labs = models.PositiveIntegerField(
        verbose_name=_('Count Labs'),
        validators=[MinValueValidator(0)],
    )
    action_date = models.DateField(
        verbose_name=_('Action Date'),
    )

    class Meta:
        indexes = [
            models.Index(fields=['action_date']),
        ]
        verbose_name = _('User Patient Activity')
        verbose_name_plural = _('User Patient Activities')

    def __str__(self) -> str:
        """
        Return a string representation of the activity, including user and patient details.

        Returns:
            String representing the activity.
        """
        return f'Daily activity by user {self.action_by_user.first_name}, {self.action_by_user.last_name} on behalf of patient {self.patient}'


class DailyUserAppActivity(models.Model):
    """
    Daily application (non-chart) activity per user.

    One record per user per day (Maximum).
    """

    action_by_user = models.ForeignKey(
        verbose_name=_('User who triggered this action'),
        to=User,
        on_delete=models.CASCADE,
        related_name='daily_user_app_activities',
    )
    last_login = models.DateTimeField(
        verbose_name=_('Last Login'),
        null=True,
    )
    count_logins = models.PositiveIntegerField(
        verbose_name=_('Count Logins'),
        validators=[MinValueValidator(0)],
    )
    count_feedback = models.PositiveIntegerField(
        verbose_name=_('Count Feedbacks'),
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
    action_date = models.DateField(
        verbose_name=_('Action Date'),
    )

    class Meta:
        indexes = [
            models.Index(fields=['action_date']),
        ]
        verbose_name = _('User App Activity')
        verbose_name_plural = _('User App Activities')

    def __str__(self) -> str:
        """
        Return a string representation of the activity.

        Returns:
            String representing the activity.
        """
        return f'Daily activity by {self.action_by_user.first_name}, {self.action_by_user.last_name}'


class DailyPatientDataReceived(models.Model):
    """Statistics of a daily data sent to patient. One record per patient per day (Maximum)."""

    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='daily_data_received',
    )
    next_appointment = models.DateTimeField(
        verbose_name=_('Next Appointment'),
        null=True,
        blank=True,
    )
    last_appointment_received = models.DateTimeField(
        verbose_name=_('Last Appointment Received'),
        null=True,
        blank=True,
    )
    appointments_received = models.PositiveIntegerField(
        verbose_name=_('Appointments Received'),
        validators=[MinValueValidator(0)],
    )
    last_document_received = models.DateTimeField(
        verbose_name=_('Last Document Received'),
        null=True,
        blank=True,
    )
    documents_received = models.PositiveIntegerField(
        verbose_name=_('Documents Received'),
        validators=[MinValueValidator(0)],
    )
    last_educational_material_received = models.DateTimeField(
        verbose_name=_('Last Educational Material Received'),
        null=True,
        blank=True,
    )
    educational_materials_received = models.PositiveIntegerField(
        verbose_name=_('Educational Materials Received'),
        validators=[MinValueValidator(0)],
    )
    last_questionnaire_received = models.DateTimeField(
        verbose_name=_('Last Questionnaire Received'),
        null=True,
        blank=True,
    )
    questionnaires_received = models.PositiveIntegerField(
        verbose_name=_('Questionnaires Received'),
        validators=[MinValueValidator(0)],
    )
    last_lab_received = models.DateTimeField(
        verbose_name=_('Last Lab Received'),
        null=True,
        blank=True,
    )
    labs_received = models.PositiveIntegerField(
        verbose_name=_('Labs Received'),
        validators=[MinValueValidator(0)],
    )
    action_date = models.DateField(
        verbose_name=_('Action Date'),
    )

    class Meta:
        indexes = [
            models.Index(fields=['action_date']),
        ]
        verbose_name = _('Patient Data Received')
        verbose_name_plural = _('Patient Data Received Records')

    def __str__(self) -> str:
        """
        Return a string representation of the data received for a patient.

        Returns:
            String representing the patient data received.
        """
        return '{patient} received data on {action_date}'.format(
            patient=str(self.patient),
            action_date=self.action_date.strftime('%Y-%m-%d'),
        )
