import pytest

from .. import factories

pytestmark = pytest.mark.django_db


def test_questionnaireprofile_factory() -> None:
    """Ensure QuestionnaireProfile factory builds properly."""
    questionnaire_profile = factories.QuestionnaireProfile()
    questionnaire_profile.full_clean()


def test_questionnaireprofile_str() -> None:
    """Ensure the `__str__` method is defined for the `QuestionnaireProfile` model."""
    questionnaire_profile = factories.QuestionnaireProfile()
    expected_follows_string = "{'19': {'title': 'Opal Feedback Questionnaire', 'lastviewed': '2022-11-17'}}"
    assert str(questionnaire_profile).split('__')[2] == expected_follows_string
