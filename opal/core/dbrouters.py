"""
Module providing DB routers for multi-database scenarios.

Specifically provides a DB router for separate handling database operations of regular and legacy DB.
"""
from typing import Any, Optional, Type

from django.db.models import Model


class LegacyDbRouter(object):
    """
    A router to ensure all legacy models use the legacy DB.

    See Django reference: https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing
    """

    legacy_app_label = 'legacy'
    legacy_db_name = 'legacy'

    def db_for_read(self, model: Type[Model], **hints: Any) -> Optional[str]:
        """
        Redirect attempts to read legacy models to the legacy DB.

        Args:
            model: the model to route to a DB connection
            hints: a dictionary of hints

        Returns:
            the DB that should be used for read operations, `None` if there is no suggestion
        """
        if model._meta.app_label == self.legacy_app_label:  # noqa: WPS437
            return self.legacy_db_name

        return None

    def db_for_write(self, model: Type[Model], **hints: Any) -> Optional[str]:
        """
        Redirect attempts to write legacy models to the legacy DB.

        Args:
            model: the model to route to a DB connection
            hints: a dictionary of hints

        Returns:
            the DB that should be used for write operations, `None` if there is no suggestion
        """
        if model._meta.app_label == self.legacy_app_label:  # noqa: WPS437
            return self.legacy_db_name

        return None
