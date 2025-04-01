# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module is used to provide configuration, fixtures, and plugins for pytest in the legacy app."""

from django.db import connections

import pytest
from _pytest.fixtures import SubRequest
from pytest_django import DjangoDbBlocker


@pytest.fixture
def clear_questionnairedb(request: SubRequest, django_db_blocker: DjangoDbBlocker) -> None:
    """
    Remove specified test data from test_QuestionnaireDB.

    Args:
        request: SubRequest object within which should be a list of tables to clear data from
        django_db_blocker: pytest fixture to allow database access here only
    """
    query_string = 'SET FOREIGN_KEY_CHECKS=0;'
    for table in request.param:
        query_string = ''.join([query_string, 'DELETE FROM ', table, ';'])
    with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
        conn.execute(query_string)
        conn.close()
