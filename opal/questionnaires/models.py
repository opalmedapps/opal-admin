"""This module provides models for questionnaires."""


from django.db import models
from django.utils.translation import gettext_lazy as _


class ExportReportPerm(models.Model):
    """Dummy model to allow for 'modelless' permissions in Questionnaires app."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('view_report', 'View Export Reports Permission'),
            ('launch_report', 'Launch Export Reports Permission'),
        )
        verbose_name = _('Export Report')
        verbose_name_plural = _('Export Reports')

    def __str__(self) -> str:
        """Return for dummy model __str__ is null."""
        pass  # noqa: DJ08, WPS420
