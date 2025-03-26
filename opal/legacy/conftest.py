"""This module is used to provide configuration, fixtures, and plugins for pytest in the legacy app."""
from typing import Any

from django.db import connections

import pytest
from pytest_django.plugin import _DatabaseBlocker


@pytest.fixture()
def clear_questionnairedb(request: Any, django_db_blocker: _DatabaseBlocker) -> None:  # noqa: PT004
    """Remove specified test data from test_QuestionnaireDB.

    Args:
        request: SubRequest object within which should be a list of tables to clear data from
        django_db_blocker: pytest fixture to allow database access here only
    """
    query_string = 'SET FOREIGN_KEY_CHECKS=0;'
    for table in request.param:
        query_string = ''.join([query_string, 'DELETE FROM ', table, ';'])
    with django_db_blocker.unblock():
        with connections['questionnaire'].cursor() as conn:
            conn.execute(query_string)
            conn.close()
