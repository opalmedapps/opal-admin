"""Test module for security question api endpoints."""
import json
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.caregivers import factories
from opal.caregivers.models import Device, DeviceType


def test_get_all_active_security_questions(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get only active security questions."""
    api_client.force_login(user=admin_user)
    security_question = factories.SecurityQuestion()
    security_question2 = factories.SecurityQuestion(is_active=False)
    response = api_client.get(reverse('api:security-questions-list'))
    assert response.status_code == HTTPStatus.OK
    assert security_question2.is_active is False
    assert response.data['count'] == 1
    assert response.data['results'][0]['title_en'] == security_question.title


def test_get_specific_active_security_question(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get a specific active security question."""
    api_client.force_login(user=admin_user)
    security_question = factories.SecurityQuestion()
    response = api_client.get(
        reverse(
            'api:security-questions-detail',
            kwargs={'pk': security_question.id},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.data['title_en'] == security_question.title


def test_get_answer_list(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get answer list could return all answer records."""
    api_client.force_login(user=admin_user)
    caregiver1 = factories.CaregiverProfile(user=admin_user)
    caregiver2 = factories.CaregiverProfile()
    security_answer1 = factories.SecurityAnswer(user=caregiver1)
    security_answer2 = factories.SecurityAnswer(user=caregiver1, answer='test')
    factories.SecurityAnswer(user=caregiver2)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-list',
            kwargs={'username': admin_user.username},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 2
    assert response.data['results'][0]['question'] == security_answer1.question
    assert response.data['results'][1]['question'] == security_answer2.question


def test_get_random_answer(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get random answer can return a correct record."""
    api_client.force_login(user=admin_user)
    caregiver = factories.CaregiverProfile(user=admin_user)
    # create only one question to test the correct data
    # cannot test random because the random result might be equal
    security_answer = factories.SecurityAnswer(user=caregiver)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-random',
            kwargs={'username': admin_user.username},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert security_answer.question == 'Apple'
    assert response.data['question'] == security_answer.question


def test_get_specific_security_answer_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get a specific security answer."""
    api_client.force_login(user=admin_user)
    caregiver = factories.CaregiverProfile(user=admin_user)
    security_answer1 = factories.SecurityAnswer(user=caregiver)
    security_answer2 = factories.SecurityAnswer(user=caregiver, question='Ananas')
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': admin_user.username, 'pk': security_answer1.id},
        ),
    )
    assert response.status_code == HTTPStatus.OK
    assert security_answer1.question != security_answer2.question
    assert response.data['question'] == security_answer1.question


def test_get_specific_security_answer_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test get a specific security answer with wrong caregiver."""
    api_client.force_login(user=admin_user)
    caregiver = factories.CaregiverProfile(user=admin_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    response = api_client.get(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': 'username2', 'pk': security_answer.id},
        ),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_specific_security_answer(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test update a specific security answer."""
    api_client.force_login(user=admin_user)
    caregiver = factories.CaregiverProfile(user=admin_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    old_answer = security_answer.answer
    new_question = {
        'question': security_answer.question,
        'answer': 'Ananas',
    }
    response = api_client.put(
        reverse(
            'api:caregivers-securityquestions-detail',
            kwargs={'username': admin_user.username, 'pk': security_answer.id},
        ),
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
    caregiver = factories.CaregiverProfile(user=admin_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': security_answer.answer}
    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'username': admin_user.username, 'pk': '{pk}'.format(pk=answer_id)},
        ),
        data=answer,
        format='json',
    )
    assert response.status_code == HTTPStatus.OK


def test_verify_answer_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test verify the user answer."""
    api_client.force_login(user=admin_user)
    caregiver = factories.CaregiverProfile(user=admin_user)
    security_answer = factories.SecurityAnswer(user=caregiver)
    answer_id = security_answer.id
    answer = {'answer': 'wrong_answer'}

    response = api_client.post(
        reverse(
            'api:caregivers-securityquestions-verify',
            kwargs={'username': admin_user.username, 'pk': '{pk}'.format(pk=answer_id)},
        ),
        data=answer,
        format='json',
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_device_put_create(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test creating a device model."""
    api_client.force_login(admin_user)
    caregiver = factories.CaregiverProfile(id=1)

    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    data = {
        'device_id': device_id,
        'type': DeviceType.IOS,
        'caregiver': caregiver.id,
        'is_trusted': False,
        'push_token': '2803df883164a7c8f12126f802a7d5fd08c361bca1e7b7a0acf88d361be54c4cc547b5a6c13141ecc5d7e',
    }

    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device_id},
        ),
        data=json.dumps(data),
        content_type='application/json',
    )

    assert response.status_code == HTTPStatus.CREATED

    assert Device.objects.count() == 1
    assert Device.objects.get().device_id == device_id


def test_device_put_update(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test updating a device model."""
    api_client.force_login(admin_user)
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(caregiver=caregiver)
    last_modified = device.modified

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

    assert response.status_code == HTTPStatus.OK

    device.refresh_from_db()

    assert device.modified > last_modified


@pytest.mark.xfail(
    condition=True,
    reason='bug that prevents the same device to be used by multiple caregivers',
    strict=True,
)
def test_device_put_two_caregivers(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test updating a device model."""
    api_client.force_login(admin_user)
    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    caregiver = factories.CaregiverProfile()
    caregiver2 = factories.CaregiverProfile()
    device = factories.Device(caregiver=caregiver, device_id=device_id)
    device2 = factories.Device(caregiver=caregiver2, device_id=device_id)

    last_modified = device.modified
    last_modified2 = device2.modified

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

    assert response.status_code == HTTPStatus.OK

    device.refresh_from_db()
    device2.refresh_from_db()

    assert device.modified > last_modified
    assert device2.modified == last_modified2


def test_create_device_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test failure for creating a device model."""
    api_client.force_login(admin_user)
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(caregiver=caregiver)

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
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
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
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
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


def test_partial_update_device_not_found(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test partial updating a device model."""
    api_client.force_login(admin_user)
    caregiver = factories.CaregiverProfile(id=1)

    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    data = {
        'device_id': device_id,
        'type': DeviceType.IOS,
        'caregiver': caregiver.id,
        'is_trusted': False,
        'push_token': '2803df883164a7c8f12126f802a7d5fd08c361bca1e7b7a0acf88d361be54c4cc547b5a6c13141ecc5d7e',
    }

    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device_id},
        ),
        data=json.dumps(data),
        content_type='application/json',
    )
    assert response_one.status_code == HTTPStatus.NOT_FOUND


def test_partial_update_device_success(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test partial updating a device model."""
    api_client.force_login(admin_user)
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(caregiver=caregiver)
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
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
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
