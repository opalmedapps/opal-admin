"""Test module for security question api endpoints."""
from collections.abc import Callable
from http import HTTPStatus

from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.caregivers import factories
from opal.users.models import User


@pytest.mark.parametrize(('url_name', 'is_detail'), [
    ('api:security-questions-list', False),
    ('api:security-questions-detail', True),
])
def test_securityquestions_unauthenticated_unauthorized(
    url_name: str,
    is_detail: bool,
    api_client: APIClient,
    user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    kwargs = {'pk': factories.SecurityQuestion().pk} if is_detail else {}
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_get_all_active_security_questions(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test get only active security questions."""
    api_client.force_login(user=user_with_permission('caregivers.view_securityquestion'))
    security_question = factories.SecurityQuestion()
    security_question2 = factories.SecurityQuestion(is_active=False)

    response = api_client.get(reverse('api:security-questions-list'))

    assert response.status_code == HTTPStatus.OK
    assert security_question2.is_active is False
    assert len(response.data) == 1
    assert response.data[0]['title_en'] == security_question.title


def test_get_specific_active_security_question(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test get a specific active security question."""
    api_client.force_login(user=user_with_permission('caregivers.view_securityquestion'))
    security_question = factories.SecurityQuestion()

    response = api_client.get(
        reverse(
            'api:security-questions-detail',
            kwargs={'pk': security_question.id},
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.data['title_en'] == security_question.title


@pytest.mark.parametrize(('url_name', 'is_detail'), [
    ('api:caregivers-securityquestions-list', False),
    ('api:caregivers-securityquestions-random', False),
    ('api:caregivers-securityquestions-detail', True),
    ('api:caregivers-securityquestions-verify', True),
])
def test_securityanswer_unauthenticated_unauthorized(
    url_name: str,
    is_detail: bool,
    api_client: APIClient,
    user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    kwargs = {'username': user.username}
    if is_detail:
        kwargs['pk'] = factories.SecurityAnswer().pk

    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_get_answer_list(api_client: APIClient, listener_user: User) -> None:
    """Test get answer list could return all answer records."""
    api_client.force_login(user=listener_user)
    caregiver1 = factories.CaregiverProfile(user=listener_user)
    caregiver2 = factories.CaregiverProfile()
    security_answer1 = factories.SecurityAnswer(user=caregiver1)
    security_answer2 = factories.SecurityAnswer(user=caregiver1, answer='test')
    factories.SecurityAnswer(user=caregiver2)

    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-list',
            kwargs={'username': listener_user.username},
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 2
    assert response.data[0]['question'] == security_answer1.question
    assert response.data[1]['question'] == security_answer2.question


def test_get_random_answer(api_client: APIClient, listener_user: User) -> None:
    """Test get random answer can return a correct record."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    # create only one question to test the correct data
    # cannot test random because the random result might be equal
    security_answer = factories.SecurityAnswer(user=caregiver)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-random',
            kwargs={'username': listener_user.username},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert security_answer.question == 'Apple'
    assert response.data['question'] == security_answer.question


def test_get_specific_security_answer_success(api_client: APIClient, listener_user: User) -> None:
    """Test get a specific security answer."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    security_answer1 = factories.SecurityAnswer(user=caregiver)
    security_answer2 = factories.SecurityAnswer(user=caregiver, question='Ananas')
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': listener_user.username, 'pk': security_answer1.id},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert security_answer1.question != security_answer2.question
    assert response.data['question'] == security_answer1.question


def test_get_specific_security_answer_failure(api_client: APIClient, listener_user: User) -> None:
    """Test get a specific security answer with wrong caregiver."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': 'username2', 'pk': security_answer.id},
        ),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_specific_security_answer(api_client: APIClient, listener_user: User) -> None:
    """Test update a specific security answer."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    old_answer = security_answer.answer
    new_question = {
        'question': security_answer.question,
        'answer': 'Ananas',
    }
    response = api_client.put(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': listener_user.username, 'pk': security_answer.id},
        ),
        data=new_question,
    )
    security_answer.refresh_from_db()
    assert response.status_code == HTTPStatus.OK
    assert security_answer.answer != old_answer
    assert security_answer.answer == 'Ananas'


def test_verify_answer_success(api_client: APIClient, listener_user: User) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': security_answer.answer}
    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'username': listener_user.username, 'pk': answer_id},
        ),
        data=answer,
    )
    assert response.status_code == HTTPStatus.OK


def test_verify_answer_failure(api_client: APIClient, listener_user: User) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=listener_user)
    caregiver = factories.CaregiverProfile(user=listener_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': 'wrong_answer'}

    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'username': listener_user.username, 'pk': answer_id},
        ),
        data=answer,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
