"""This module provides models for questionnaires."""
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

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
    )
    questionnaire_list = models.JSONField(
        verbose_name=_('Questionnaire List'),
        blank=True,
        null=True,
        default=dict,
    )

    class Meta:
        verbose_name = _('Questionnaire Profile')
        verbose_name_plural = _('Questionnaire Profiles')

    def __str__(self) -> str:
        """Questionnaire profile to string.

        Returns:
            username with the following questionnaire list
        """
        return '{user}__follows__{qstList}'.format(user=self.user.username, qstList=self.questionnaire_list)
