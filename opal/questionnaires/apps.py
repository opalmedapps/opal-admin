"""Module providing configuration for the questionnaires app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QuestionnairesConfig(AppConfig):
    """The app configuration for the questionnaires app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.questionnaires'
    verbose_name = _('Questionnaires')
