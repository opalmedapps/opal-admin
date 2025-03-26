"""This module provides models for hospital-specific settings."""

from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..core.models import Address


class Location(models.Model):
    """Abstract class representing a hospital location with a name and code."""

    name = models.CharField(_('Name'), max_length=100)
    acronym = models.CharField(_('Acronym'), max_length=10, unique=True, default='')

    class Meta:
        abstract = True

    def __str__(self) -> str:
        """
        Return the string representation of the location.

        Returns:
            the name of the location
        """
        return self.name


class Institution(Location):  # type: ignore[django-manager-missing]
    """A hospital institution."""

    terms_of_use = models.FileField(
        verbose_name=_('Terms of use'),
        upload_to='uploads/%Y/%m/%d/',  # noqa: WPS323
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    logo = models.ImageField(
        _('Logo'),
        upload_to='uploads/institution-logo/',
    )
    support_email = models.EmailField(
        verbose_name=_('Support email'),
    )
    adulthood_age = models.PositiveIntegerField(
        verbose_name=_('Adulthood Age'),
        help_text=_('Age setting used to control pediatric functionality which delays sharing of lab results.'),
        default=18,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99),
        ],
    )
    non_interpretable_lab_result_delay = models.PositiveIntegerField(
        verbose_name=_('Non-Interpretable Lab Result Delay'),
        help_text=_(
            'Lab result delay for pediatric patients when clinician interpretation is recommended in lab setting.',
        ),
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99),
        ],
    )
    interpretable_lab_result_delay = models.PositiveIntegerField(
        verbose_name=_('Interpretable Lab Result Delay'),
        help_text=_(
            'Lab result delay for pediatric patients when clinician interpretation is not specified in lab setting.',
        ),
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99),
        ],
    )
    registration_code_valid_period = models.PositiveIntegerField(
        verbose_name=_('Registration Code Valid Period'),
        help_text=_(
            'Valid period of a registration code generated by the QR code generator.',
        ),
        default=72,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        permissions = (('can_manage_institutions', _('Can manage institutions')),)
        ordering = ['name']
        verbose_name = _('Institution')
        verbose_name_plural = _('Institutions')


class Site(Location, Address):  # type: ignore[django-manager-missing]
    """A site belonging to an [Institution][opal.hospital_settings.models.Institution] with its specific properties."""

    parking_url = models.URLField(_('Parking Info (URL)'))
    direction_url = models.URLField(_('Getting to the Hospital (URL)'))
    institution = models.ForeignKey(
        to=Institution,
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('Institution'),
    )
    longitude = models.DecimalField(
        max_digits=22,
        decimal_places=16,
        default=None,
        verbose_name=_('Longitude'),
    )
    latitude = models.DecimalField(
        max_digits=22,
        decimal_places=16,
        default=None,
        verbose_name=_('Latitude'),
    )

    class Meta:
        permissions = (('can_manage_sites', _('Can manage sites')),)
        ordering = ['name']
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')
