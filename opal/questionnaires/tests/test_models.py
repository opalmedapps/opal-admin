import pytest

from .. import factories, models

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


def test_questionnaireprofile_update() -> None:
    """Ensure QuestionnaireProfile factory builds properly."""
    questionnaire_profile = factories.QuestionnaireProfile()
    models.QuestionnaireProfile.update_questionnaires_following(
        qid='13',
        qname='Test Qst Add',
        user=questionnaire_profile.user,
        toggle=True,
    )
    retrieve_profile, created = models.QuestionnaireProfile.objects.get_or_create(user=questionnaire_profile.user)

    assert '13' in retrieve_profile.questionnaire_list
    assert len(retrieve_profile.questionnaire_list) == 2
    assert not created  # Should not need to create a new profile


def test_questionnaireprofile_toggle_off() -> None:
    """Ensure QuestionnaireProfile factory builds properly."""
    questionnaire_profile = factories.QuestionnaireProfile()
    models.QuestionnaireProfile.update_questionnaires_following(
        qid='19',
        qname='Test Qst Add',
        user=questionnaire_profile.user,
        toggle=False,
    )
    retrieve_profile, created = models.QuestionnaireProfile.objects.get_or_create(user=questionnaire_profile.user)

    assert not retrieve_profile.questionnaire_list
    assert not created
