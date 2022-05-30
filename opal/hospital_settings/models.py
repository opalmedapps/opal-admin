"""This module provides models for hospital-specific settings."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    """Abstract class representing a hospital location with a name and code."""

    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=10, unique=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        """
        Return the string representation of the location.

        Returns:
            the name of the location
        """
        return self.name


class Institution(Location):
    """A hospital institution."""

    class Meta:
        ordering = ['name']
        verbose_name = _('Institution')
        verbose_name_plural = _('Institutions')


class Site(Location):
    """A site belonging to an [Institution][opal.hospital_settings.models.Institution] with its specific properties."""

    parking_url = models.URLField(_('Parking Info (URL)'))
    direction_url = models.URLField(_('Getting to the Hospital (URL)'))
    institution = models.ForeignKey(
        to=Institution,
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('Institution'),
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')
