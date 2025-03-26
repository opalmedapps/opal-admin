"""
Module providing DB routers for multi-database scenarios.

Specifically provides a DB router for separate handling database operations of regular and legacy DBs.
"""
from typing import Any, Optional

from django.db.models import Model


class LegacyDbRouter(object):
    """
    A router to ensure all legacy models use the appropriate legacy DB.

    See Django reference: https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing
    """

    legacy_app_label = 'legacy'
    legacy_db_name = 'legacy'
    legacy_questionnaire_app_label = 'legacy_questionnaires'
    legacy_questionnaire_db_name = 'questionnaire'

    def db_for_read(self, model: type[Model], **hints: Any) -> Optional[str]:
        """
        Redirect attempts to read legacy models to the legacy DBs.

        Args:
            model: the model to route to a DB connection
            hints: a dictionary of hints

        Returns:
            the DB that should be used for read operations, `None` if there is no suggestion
        """
        if model._meta.app_label == self.legacy_app_label:
            return self.legacy_db_name
        elif model._meta.app_label == self.legacy_questionnaire_app_label:
            return self.legacy_questionnaire_db_name

        return None

    def db_for_write(self, model: type[Model], **hints: Any) -> Optional[str]:
        """
        Redirect attempts to write legacy models to the legacy DBs.

        Args:
            model: the model to route to a DB connection
            hints: a dictionary of hints

        Returns:
            the DB that should be used for write operations, `None` if there is no suggestion
        """
        if model._meta.app_label == self.legacy_app_label:
            return self.legacy_db_name
        elif model._meta.app_label == self.legacy_questionnaire_app_label:
            return self.legacy_questionnaire_db_name

        return None
