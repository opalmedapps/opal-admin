from django.conf import settings

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


def test_get_all_questionnaires(questionnaire_data: None) -> None:
    """Test data is being returned."""
    response = queries.get_all_questionnaires(1)

    assert len(response) == 65


def test_get_all_questionnaires_db_error(django_db_blocker: DjangoDbBlocker) -> None:
    """Test error thrown when empty questionnairedb is provided."""
    response = queries.get_all_questionnaires(2)

    assert response == [{}]
