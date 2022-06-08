"""This module provides models for report templates' settings."""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ReportTemplate(models.Model):
    """Report template with its specific settings."""

    name = models.CharField(_('Name'), max_length=25)
    logo = models.ImageField(_('Logo'))
    header = models.CharField(_('Header'), max_length=50)
    slug = models.SlugField(unique=True)
    favicon = models.CharField(max_length=50)

    class Meta:
        verbose_name = _('Report Template')
        verbose_name_plural = _('Report Templates')

    def __str__(self) -> str:
        """
        Return the string representation of the report template.

        Returns:
            the name of the class
        """
        return self.name

    def get_absolute_url(self) -> str:
        """
        Return the URL for a given object using slug.

        Returns:
            str: object's URL that uniquely identifies
        """
        return reverse('report-settings:template-update', kwargs={'slug': self.slug})
