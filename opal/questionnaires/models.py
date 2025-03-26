"""This module provides models for questionnaires."""


from django.db import models
from django.utils.translation import gettext_lazy as _


class ExportReportPermission(models.Model):  # noqa: DJ08
    """Dummy model to allow for 'modelless' permissions in Questionnaires app."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('export_report', 'Export Reports Permission'),
        )
        verbose_name = _('Export Report')
        verbose_name_plural = _('Export Reports')
