from django.conf import settings
from django.db import connections

import pytest
from pytest_django import DjangoDbBlocker

from .. import queries

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_set_test_account_string_debug_false() -> None:
    """Test the setting of test account string when not in debug mode."""
    test_accounts = queries.set_test_account(False)
    assert test_accounts == ', '.join(map(str, settings.TEST_PATIENTS))


def test_set_test_account_string_debug() -> None:
    """Test the setting of test account string when in debug mode."""
    test_accounts = queries.set_test_account(True)
    assert test_accounts == ('-1')


def test_get_all_questionnaires_db_error(django_db_blocker: DjangoDbBlocker) -> None:
    """Test error thrown when empty questionnairedb is provided."""
    with django_db_blocker.unblock():
        with connections['questionnaire'].cursor() as conn:
            conn.execute('SET FOREIGN_KEY_CHECKS=0; DELETE FROM answer;DELETE FROM questionnaire;')
            conn.close()

    response = queries.get_all_questionnaires(2)
    assert response == [{}]
