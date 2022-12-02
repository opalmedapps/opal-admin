"""Module providing models for the health data app."""
from enum import Enum
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


class HealthDataStore(models.Model):
    patient = models.ForeignKey(to=Patient, on_delete=models.CASCADE, related_name='health_data_store')

    class Meta:
        verbose_name = _('Health Data Store')
        verbose_name_plural = _('Health Data Stores')

    def __str__(self) -> str:
        return f'Health Data Store for {self.patient}'


class AbstractSample(models.Model):
    source = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-start_date',)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError(f'Cannot change an existing instance of {self._meta.verbose_name}')
        return super().save(*args, **kwargs)


class QuantitySampleType(models.TextChoices):
    HEART_RATE = 'HR', _('Heart Rate (bpm)')
    HEART_RATE_VARIABILITY = 'HRV', _('Heart Rate Variability (ms))')
    OXYGEN_SATURATION = 'SPO2', _('Oxygen Saturation (%)')
    BODY_MASS = 'BM', _('Body Mass (kg)')


class Unit(Enum):
    BEATS_PER_MINUTE = 'bpm'
    MILLISECONDS = 'ms'
    PERCENT = '%'
    KILOGRAM = 'kg'


class QuantitySample(AbstractSample):
    data_store = models.ForeignKey(to=HealthDataStore, on_delete=models.CASCADE, related_name='quantity_samples')
    value = models.DecimalField(max_digits=7, decimal_places=2)
    type = models.CharField(choices=QuantitySampleType.choices, max_length=4)  # noqa: A003

    class Meta:
        verbose_name = _('Quantity Sample')
        verbose_name_plural = _('Quantity Samples')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_type_valid',  # noqa: WPS323
                check=models.Q(type__in=QuantitySampleType.values),
            ),
        ]

    def __str__(self) -> str:
        sample_type = QuantitySampleType(self.type)
        unit_text = sample_type.label.split('(')[1][:-1]
        unit = Unit(unit_text)

        return f'{self.value} {unit.value}'


@receiver(post_save, sender=Patient)
def update_patient(sender, instance, created: bool, **kwargs):
    print('update patient signal')
    if created:
        HealthDataStore.objects.create(patient=instance)
