"""Test module for security question api endpoints."""
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers.factories import SecurityAnswer, SecurityQuestion


def test_get_all_active_security_questions(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get only active security questions."""
    api_client.force_login(user=admin_user)
    security_question = SecurityQuestion()
    security_question2 = SecurityQuestion(is_active=False)
    response = api_client.get(reverse('api:security-questions'))
    assert response.status_code == 200
    assert security_question2.is_active is False
    assert len(response.data) == 1
    assert security_question.title == 'Apple'
    assert response.data[0]['title'] == security_question.title


def test_get_random_question(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get_random_question can return a correct record."""
    api_client.force_login(user=admin_user)
    # create only one question to test the correct data
    # cannot test random because the random result might be equal
    security_question = SecurityQuestion()
    response = api_client.get(reverse('api:random-question'))
    assert response.status_code == 200
    assert security_question.title == 'Apple'
    assert response.data['title'] == security_question.title


def test_update_security_question(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test update a security question."""
    api_client.force_login(user=admin_user)
    security_question = SecurityQuestion()
    new_question = {
        'title': security_question.title,
        'title_en': security_question.title,
        'title_fr': 'Ananas',
    }
    print(new_question)
    response = api_client.put(
        reverse('api:update-question'),
        data=new_question,
        format='json',
    )
    assert response.status_code == 200


def test_verify_answer(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=admin_user)
    security_question = SecurityQuestion()
    security_answer = SecurityAnswer()
    question_id = security_question.id
    answer = {'answer': security_answer.answer}
    response = api_client.post(
        reverse(
            'api:verify-answer',
            kwargs={'question_id': '{question_id}'.format(question_id=question_id)},
        ),
        data=answer,
        format='json',
    )
    assert response.status_code == 200
