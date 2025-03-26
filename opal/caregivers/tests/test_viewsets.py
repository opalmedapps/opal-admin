"""Test module for security question api endpoints."""
import json
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers.factories import CaregiverProfile, Device, SecurityAnswer, SecurityQuestion
from opal.caregivers.models import DeviceType


def test_get_all_active_security_questions(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get only active security questions."""
    api_client.force_login(user=admin_user)
    security_question = SecurityQuestion()
    security_question2 = SecurityQuestion(is_active=False)
    response = api_client.get(reverse('api:security-questions-list'))
    assert response.status_code == HTTPStatus.OK
    assert security_question2.is_active is False
    assert response.data['count'] == 1
    assert response.data['results'][0]['title_en'] == security_question.title


def test_get_answer_list(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get answer list could return all answer records."""
    api_client.force_login(user=admin_user)
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    security_answer1 = SecurityAnswer(user=caregiver1)
    security_answer2 = SecurityAnswer(user=caregiver1, answer='test')
    SecurityAnswer(user=caregiver2)
    response = api_client.get(reverse('api:caregivers-securityquestions-list', kwargs={'uuid': caregiver1.uuid}))
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 2
    assert response.data['results'][0]['question'] == security_answer1.question
    assert response.data['results'][1]['question'] == security_answer2.question


def test_get_random_answer(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get random answer can return a correct record."""
    api_client.force_login(user=admin_user)
    caregiver = CaregiverProfile()
    # create only one question to test the correct data
    # cannot test random because the random result might be equal
    security_answer = SecurityAnswer(user=caregiver)
    response = api_client.get(reverse('api:caregivers-securityquestions-random', kwargs={'uuid': caregiver.uuid}))
    assert response.status_code == HTTPStatus.OK
    assert security_answer.question == 'Apple'
    assert response.data['question'] == security_answer.question


def test_get_specific_security_answer_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get a specific security answer."""
    api_client.force_login(user=admin_user)
    caregiver = CaregiverProfile()
    security_answer1 = SecurityAnswer(user=caregiver)
    security_answer2 = SecurityAnswer(user=caregiver, question='Ananas')
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'uuid': caregiver.uuid, 'pk': security_answer1.id},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert security_answer1.question != security_answer2.question
    assert response.data['question'] == security_answer1.question


def test_get_specific_security_answer_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get a specific security answer with wrong caregiver."""
    api_client.force_login(user=admin_user)
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    security_answer = SecurityAnswer(user=caregiver1)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'uuid': caregiver2.uuid, 'pk': security_answer.id},
        ),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_specific_security_answer(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test update a specific security answer."""
    api_client.force_login(user=admin_user)
    caregiver = CaregiverProfile()
    security_answer = SecurityAnswer(user=caregiver)
    old_answer = security_answer.answer
    new_question = {
        'question': security_answer.question,
        'answer': 'Ananas',
    }
    response = api_client.put(
        reverse('api:caregivers-securityquestions-detail', kwargs={'uuid': caregiver.uuid, 'pk': security_answer.id}),
        data=new_question,
        format='json',
    )
    security_answer.refresh_from_db()
    assert response.status_code == HTTPStatus.OK
    assert security_answer.answer != old_answer
    assert security_answer.answer == 'Ananas'


def test_verify_answer_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=admin_user)
    caregiver = CaregiverProfile()
    security_answer = SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': security_answer.answer}
    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'uuid': caregiver.uuid, 'pk': '{pk}'.format(pk=answer_id)},
        ),
        data=answer,
        format='json',
    )
    assert response.status_code == HTTPStatus.OK


def test_verify_answer_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=admin_user)
    caregiver = CaregiverProfile()
    security_answer = SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': 'wrong_answer'}

    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'uuid': caregiver.uuid, 'pk': '{pk}'.format(pk=answer_id)},
        ),
        data=answer,
        format='json',
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_device_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test creating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver)

    data = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data),
        content_type='application/json',
    )
    device.full_clean()
    assert response.status_code == HTTPStatus.OK


def test_create_device_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test failure for creating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver)

    data = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': 'bad_caregiver_pk',
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data),
        content_type='application/json',
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_device_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test updating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver, type=DeviceType.IOS, push_token='aaaa1111', is_trusted=False)  # noqa: S106
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_one),
        content_type='application/json',
    )
    # Change device data for full update action
    data_two = {
        'device_id': device.device_id,
        'type': DeviceType.ANDROID,
        'caregiver': caregiver.id,
        'is_trusted': True,
        'push_token': 'bbbb2222',
    }
    response_two = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_two),
        content_type='application/json',
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.OK


def test_update_device_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test failure for updating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver, type=DeviceType.IOS, push_token='aaaa1111', is_trusted=False)  # noqa: S106
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_one),
        content_type='application/json',
    )
    # Input invalid data
    data_two = {
        'device_id': device.device_id,
        'type': DeviceType.ANDROID,
        'caregiver': caregiver.id,
        'is_trusted': 'fish',
        'push_token': 'bbbb2222',
    }
    response_two = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_two),
        content_type='application/json',
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.BAD_REQUEST


def test_partial_update_device_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test partial updating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver)
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_one),
        content_type='application/json',
    )
    assert response_one.status_code == HTTPStatus.OK


def test_partial_update_device_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test failure for partial updating a device model."""
    api_client.force_login(admin_user)
    caregiver = CaregiverProfile(id=1)
    device = Device(caregiver=caregiver, type=DeviceType.IOS, push_token='aaaa1111', is_trusted=False)  # noqa: S106
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_one),
        content_type='application/json',
    )
    # Input invalid data
    data_two = {
        'device_id': device.device_id,
        'caregiver': caregiver.id,
        'is_trusted': 'fish',
    }
    response_two = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=json.dumps(data_two),
        content_type='application/json',
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.BAD_REQUEST
