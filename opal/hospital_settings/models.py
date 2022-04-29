"""This module provides models for hospital-specific settings."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import constants


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


class RelationshipType(models.Model):
    """A type of relationship between a user (aka caregiver) and patient."""

    name = models.CharField(_('Name'), max_length=25)
    description = models.CharField(_('Description'), max_length=200)
    start_age = models.PositiveIntegerField(
        _('Start age'),
        help_text=_('Minimum age the relationship is allowed to start.'),
        validators=[
            MinValueValidator(constants.RELATIONSHIP_MIN_AGE),
            MaxValueValidator(constants.RELATIONSHIP_MAX_AGE - 1),
        ])
    end_age = models.PositiveIntegerField(
        _('End age'),
        help_text=_('Age at which the relationship ends automatically.'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(constants.RELATIONSHIP_MIN_AGE + 1),
            MaxValueValidator(constants.RELATIONSHIP_MAX_AGE),
        ])
    form_required = models.BooleanField(
        _('Form required'),
        default=True,
        help_text=_('Whether the hospital form is required to be completed by the caregiver'),
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Caregiver Relationship Type')
        verbose_name_plural = _('Caregiver Relationship Types')

    def __str__(self) -> str:
        """Return the string representation of the User Patient Relationship Type.

        Returns:
            the name of the user patient relationship type
        """
        return self.name
