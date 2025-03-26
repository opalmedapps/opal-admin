"""
Module providing models for the health data app.

These models facilitate the collection and storage of health data
provided by various sources (such as the patient, a clinician) and (smart) devices.

The models in this module are inspired by Apple HealthKit, such as:
    * https://developer.apple.com/documentation/healthkit
    * https://developer.apple.com/documentation/healthkit/hkquantity
    * https://developer.apple.com/documentation/healthkit/hkquantitysample
    * https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier
    * https://developer.apple.com/documentation/healthkit/hkelectrocardiogram
"""
from enum import Enum
from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


class HealthDataStore(models.Model):
    """A storage for health data for a specific patient.

    The `HealthDataStore` model is the connection between this app and the `patients` app.
    Each patient can have one health data store.
    """

    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='health_data_store',
    )

    class Meta:
        verbose_name = _('Health Data Store')
        verbose_name_plural = _('Health Data Stores')

    def __str__(self) -> str:
        """
        Return the textual representation of this instance including the patient name.

        Returns:
            the textual representation of this health data store
        """
        return f'Health Data Store for {self.patient}'


class SampleSourceType(models.TextChoices):
    """The source a sample was provided by."""

    PATIENT = 'P', _('Patient')
    CLINICIAN = 'C', _('Clinician')


class AbstractSample(models.Model):
    """An abstract sample for all measurements of health data.

    This model should be inherited from by all concrete sample models.
    """

    start_date = models.DateTimeField(_('Start Date'))
    device = models.CharField(
        _('Device'),
        max_length=255,
        help_text=_('The device that was used to take the measurement'),
    )
    source = models.CharField(
        _('Source'),
        max_length=1,
        choices=SampleSourceType.choices,
        help_text=_('The source that provided this sample, for example, the patient if it is patient-reported data'),
    )
    added_at = models.DateTimeField(
        _('Added At'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ('-start_date',)
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_source_valid',
                check=models.Q(type__in=SampleSourceType.values),
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the current instance.

        Prevents changing an instance once it was saved the first time.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Raises:
            ValidationError: if attempting to save an already existing instance
        """
        if self.pk:
            raise ValidationError(f'Cannot change an existing instance of {self._meta.verbose_name}')

        super().save(*args, **kwargs)


class QuantitySampleType(models.TextChoices):
    """
    The type of a quantity sample.

    Currently, the unit of the type needs to be provided as part of the label at the end, in parentheses.
    For example, 'Body Temperature (°C)'.
    The unit needs to be defined in the `Unit` enum.
    """

    BODY_MASS = 'BM', _('Body Mass (kg)')
    BODY_TEMPERATURE = 'TMP', _('Body Temperature (°C)')
    HEART_RATE = 'HR', _('Heart Rate (bpm)')
    HEART_RATE_VARIABILITY = 'HRV', _('Heart Rate Variability (ms))')
    OXYGEN_SATURATION = 'SPO2', _('Oxygen Saturation (%)')


class Unit(Enum):
    """An enumeration of supported units for sample types."""

    BEATS_PER_MINUTE = 'bpm'
    CELSIUS = '°C'
    KILOGRAM = 'kg'
    MILLISECONDS = 'ms'
    PERCENT = '%'


class QuantitySample(AbstractSample):
    """
    A quantity sample represents a single measurement with a numeric value and type (i.e., unit).

    Inspired by Apple Health Kit's `HKQuantitySample`:
    https://developer.apple.com/documentation/healthkit/hkquantitysample
    """

    data_store = models.ForeignKey(
        verbose_name=_('Health Data Store'),
        to=HealthDataStore,
        on_delete=models.CASCADE,
        related_name='quantity_samples',
    )
    value = models.DecimalField(
        _('Value'),
        max_digits=7,
        decimal_places=2,
    )
    type = models.CharField(  # noqa: A003
        _('Type'),
        choices=QuantitySampleType.choices,
        max_length=4,
    )

    class Meta:
        verbose_name = _('Quantity Sample')
        verbose_name_plural = _('Quantity Samples')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',
                check=models.Q(type__in=QuantitySampleType.values),
            ),
        ]

    def __str__(self) -> str:
        """
        Return the value and unit of this instance.

        The unit is extracted from the `QuantitySampleType` label.

        Returns:
            the textual representation of this instance
        """
        sample_type = QuantitySampleType(self.type)
        unit_text = sample_type.label.split('(')[1][:-1]
        unit = Unit(unit_text)

        return f'{self.value} {unit.value}'


@receiver(post_save, sender=Patient)
def patient_saved(sender: Type[Patient], instance: Patient, created: bool, **kwargs: Any) -> None:
    """
    Post save signal to create a `HealthDataStore` for a patient when the `Patient` is created.

    See: https://docs.djangoproject.com/en/dev/ref/signals/#post-save

    Args:
        sender: the model class
        instance: the actual instance being saved
        created: whether a new record was created
        kwargs: additional keyword arguments
    """
    if created:
        HealthDataStore.objects.create(patient=instance)
