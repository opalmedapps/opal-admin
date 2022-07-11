"""This module provides models for hospital-specific settings."""

import os

from django.conf import settings
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

    logo = models.ImageField(
        _('Logo'),
        upload_to='uploads/institution-logo/',
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Institution')
        verbose_name_plural = _('Institutions')


    def save(self, *args, **kwargs) -> None:
        _, f_en_extension = os.path.splitext(self.logo.name)
        _, f_fr_extension = os.path.splitext(self.logo_fr.name)

        try:
            this = Institution.objects.get(id=self.id)
            if this.logo != self.logo:
                os.remove(this.logo.path)

                self.logo.name = '{0}_{1}{2}'.format(self.code, 'logo_en', f_en_extension)

            if this.logo_fr != self.logo_fr:
                os.remove(this.logo_fr.path)

                self.logo_fr.name = '{0}_{1}{2}'.format(self.code, 'logo_fr', f_fr_extension)

            if this.code != self.code and this.logo == self.logo:
                new_name = 'uploads/institution-logo/{0}_{1}{2}'.format(
                    self.code,
                    'logo_en',
                    f_en_extension,
                )
                new_path = '{0}/{1}'.format(settings.MEDIA_ROOT, new_name)
                os.rename(this.logo.path, new_path)
                self.logo.name = new_name

            if this.code != self.code and this.logo_fr == self.logo_fr:
                new_name = 'uploads/institution-logo/{0}_{1}{2}'.format(
                    self.code,
                    'logo_fr',
                    f_fr_extension,
                )
                new_path = '{0}/{1}'.format(settings.MEDIA_ROOT, new_name)
                os.rename(this.logo_fr.path, new_path)
                self.logo_fr.name = new_name
        except Exception:
            self.logo.name = '{0}_{1}{2}'.format(self.code, 'logo_en', f_en_extension)
            self.logo_fr.name = '{0}_{1}{2}'.format(self.code, 'logo_fr', f_fr_extension)

        super(Institution, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # check https://stackoverflow.com/questions/16041232/django-delete-filefield
        # django cleanup
        # your data might end up referencing a nonexistent file if your save() method call happens to be within a transaction that gets rolled back.
        if os.path.isfile(self.logo.path):
            os.remove(self.logo.path)
        if os.path.isfile(self.logo_fr.path):
            os.remove(self.logo_fr.path)
        super(Institution, self).delete(*args, **kwargs)


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
        ordering = ['name']
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')
