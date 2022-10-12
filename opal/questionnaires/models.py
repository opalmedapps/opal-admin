"""This module provides models for questionnaires."""
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


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


class QuestionnaireProfile(models.Model):
    """Model used for tracking a list of saved questionnaires per-user."""

    uuid = models.UUIDField(
        verbose_name=_('UUID'),
        unique=True,
        default=uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
    )
    questionnaires = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        verbose_name = _('Questionnaire Profile')
        verbose_name_plural = _('Questionnaire Profiles')

    def __str__(self) -> str:
        """Questionnaire profile to string.

        Returns:
            username
        """
        return self.user.username
