# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides models for questionnaires."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


class Questionnaire(models.Model):  # noqa: DJ008
    """
    Empty model to allow for 'modelless' permissions in Questionnaires app.

    This model is intended to be the future model for a questionnaire once we migrate them.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (('export_report', 'Export Reports'),)
        verbose_name = _('Questionnaire')
        verbose_name_plural = _('Questionnaires')


class QuestionnaireProfile(models.Model):
    """Model used for tracking a list of saved questionnaires per-user."""

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.CASCADE,
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
        """
        Questionnaire profile to string.

        Returns:
            username with the following questionnaire list
        """
        return f'{self.user.username}__follows__{self.questionnaire_list}'

    @classmethod
    def update_questionnaires_following(cls, qid: str, qname: str, user: User, toggle: bool) -> None:
        """
        Update the questionnaires following list for specific user.

        Args:
            qid: questionnaire id number
            qname: questionnaire title
            user: requesting user object
            toggle: add or remove qid from list
        """
        questionnaires_following, _ = cls.objects.get_or_create(
            user=user,
        )
        if toggle:
            questionnaires_following.questionnaire_list[qid] = {
                'title': qname,
                'lastviewed': timezone.now().date().isoformat(),
            }
        elif qid in questionnaires_following.questionnaire_list:
            questionnaires_following.questionnaire_list.pop(qid)
        questionnaires_following.save()
