"""This module provides models for questionnaires."""
from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


class Questionnaire(models.Model):  # noqa: DJ08 (currently not a model that is instantiated)
    """Dummy model to allow for 'modelless' permissions in Questionnaires app."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('export_report', 'Export Reports'),
        )
        verbose_name = _('Questionnaire')
        verbose_name_plural = _('Questionnaires')


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

    @classmethod
    def update_questionnaires_following(cls, qid: str, qname: str, user: User, toggle: bool) -> None:
        """Update the questionnaires following list for specific user.

        Args:
            qid: questionnaire id number
            qname: questionnaire title
            user: requesting user object
            toggle: add or remove qid from list
        """
        questionnaires_following, _ = cls.objects.get_or_create(
            user=user,
        )
        if (toggle):
            questionnaires_following.questionnaire_list[qid] = {
                'title': qname,
                'lastviewed': datetime.now().strftime('%Y-%m-%d'),
            }
        elif qid in questionnaires_following.questionnaire_list:
            questionnaires_following.questionnaire_list.pop(qid)
        questionnaires_following.save()
