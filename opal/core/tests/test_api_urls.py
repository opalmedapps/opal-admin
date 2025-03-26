import sys
from importlib import reload

from django.urls import NoReverseMatch, Resolver404, resolve, reverse

import pytest
from pytest_django.fixtures import SettingsWrapper


def test_api_root_debug_only(settings: SettingsWrapper) -> None:
    """Ensure that the API root is available in debug mode."""
    path = '/{api_root}/'.format(api_root=settings.API_ROOT)
    assert reverse('api:api-root') == path
    assert resolve(path).view_name == 'api:api-root'


# reload API URLs to force debug=False
# since the URLs are loaded at startup time
# pytest-django sets debug_mode to false but it happens later
# see: https://stackoverflow.com/a/59984680
@pytest.mark.urls('opal.core.api_urls')
def test_api_root_not_accessible_in_non_debug(settings: SettingsWrapper) -> None:
    """Ensure that the API root is not available when not in debug mode."""
    assert settings.DEBUG is False
    path = '/{api_root}/'.format(api_root=settings.API_ROOT)

    # reload API URLs module with debug=False to record coverage properly
    # see: https://stackoverflow.com/a/46034755
    reload(sys.modules['opal.core.api_urls'])

    with pytest.raises(NoReverseMatch):
        reverse('api:api-root')
    with pytest.raises(Resolver404):
        resolve(path)


def test_api_auth_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API auth endpoints are defined."""
    auth_login_path = '/{api_root}/auth/login/'.format(api_root=settings.API_ROOT)
    assert reverse('api:rest_login') == auth_login_path
    assert resolve(auth_login_path).view_name == 'api:rest_login'


def test_api_languages_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API languages endpoints are defined."""
    languages_path = '/{api_root}/languages/'.format(api_root=settings.API_ROOT)
    assert reverse('api:languages') == languages_path
    assert resolve(languages_path).view_name == 'api:languages'


def test_api_app_chart_defined(settings: SettingsWrapper) -> None:
    """
    Ensure that the REST API app chart endpoints are defined.

    PatientSernum 51 is define in DBV for testing purpose.
    """
    legacy_db_patient_sernum = 51
    app_chart_path = '/{api_root}/app/chart/{legacy_id}/'.format(
        api_root=settings.API_ROOT,
        legacy_id=legacy_db_patient_sernum,
    )
    assert reverse('api:app-chart', kwargs={'legacy_id': legacy_db_patient_sernum}) == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:app-chart'


def test_api_app_appointments_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API app appointments endpoints are defined."""
    app_apointments_path = '/{api_root}/app/appointments/'.format(
        api_root=settings.API_ROOT,
    )
    assert reverse('api:app-appointments') == app_apointments_path
    assert resolve(app_apointments_path).view_name == 'api:app-appointments'


def test_api_check_permissions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API check-permissions endpoint is defined."""
    check_permissions_path = '/{api_root}/patients/legacy/{legacy_id}/check-permissions/'.format(
        api_root=settings.API_ROOT,
        legacy_id=1,
    )
    assert reverse('api:caregiver-permissions', kwargs={'legacy_id': 1}) == check_permissions_path
    assert resolve(check_permissions_path).view_name == 'api:caregiver-permissions'


def test_api_security_questions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API security questions endpoints are defined."""
    question_path = '/{api_root}/security-questions/'.format(api_root=settings.API_ROOT)
    assert reverse('api:security-questions-list') == question_path
    assert resolve(question_path).view_name == 'api:security-questions-list'


def test_api_caregiver_security_questions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions are defined."""
    question_path = '/{api_root}/caregivers/{username}/security-questions/123/'.format(
        api_root=settings.API_ROOT,
        username='username',
    )
    assert reverse(
        'api:caregivers-securityquestions-detail',
        kwargs={'username': 'username', 'pk': 123},
    ) == question_path
    assert resolve(question_path).view_name == 'api:caregivers-securityquestions-detail'


def test_api_caregiver_patient_list_defined(settings: SettingsWrapper) -> None:
    """Ensure that the API for retrieving a caregiver's patients is defined."""
    url = f'/{settings.API_ROOT}/caregivers/patients/'

    assert reverse('api:caregivers-patient-list') == url
    assert resolve(url).view_name == 'api:caregivers-patient-list'


def test_api_caregiver_detail_defined(settings: SettingsWrapper) -> None:
    """Ensure that the API for retrieving a caregiver's profile is defined."""
    url = f'/{settings.API_ROOT}/caregivers/username/'

    assert reverse('api:caregivers-detail', kwargs={'username': 'username'}) == url
    assert resolve(url).view_name == 'api:caregivers-detail'


def test_api_security_question_random_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions random endpoints are defined."""
    question_path = '/{api_root}/caregivers/{username}/security-questions/random/'.format(
        api_root=settings.API_ROOT,
        username='username',
    )
    assert reverse(
        'api:caregivers-securityquestions-random',
        kwargs={'username': 'username'},
    ) == question_path
    assert resolve(question_path).view_name == 'api:caregivers-securityquestions-random'


def test_api_verify_secruity_answer_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions verify endpoints are defined."""
    question_path = 'caregivers/username/security-questions/123/verify/'
    question_path = '/{api_root}/{question_path}'.format(api_root=settings.API_ROOT, question_path=question_path)
    assert reverse(
        'api:caregivers-securityquestions-verify',
        kwargs={'username': 'username', 'pk': 123},
    ) == question_path
    assert resolve(question_path).view_name == 'api:caregivers-securityquestions-verify'


# questionnaire report generation API endpoint: questionnaires/reviewed/
def test_questionnaires_reviewed(settings: SettingsWrapper) -> None:
    """Ensure `questionnaires/reviewed/` endpoint is defined."""
    url_path = '/{api_root}/questionnaires/reviewed/'.format(api_root=settings.API_ROOT)
    assert reverse('api:questionnaires-reviewed') == url_path
    assert resolve(url_path).view_name == 'api:questionnaires-reviewed'


def test_retrieve_registration_code(settings: SettingsWrapper) -> None:
    """Ensure `registration/<str:code>/` endpoint is defined."""
    registration_code = 'ABCD12345678'
    url_path = '/{api_root}/registration/{code}/'.format(
        api_root=settings.API_ROOT,
        code=registration_code,
    )
    assert reverse('api:registration-code', kwargs={'code': registration_code}) == url_path
    assert resolve(url_path).view_name == 'api:registration-code'


def test_retrieve_registration_register(settings: SettingsWrapper) -> None:
    """Ensure `registration/<str:code>/register/` endpoint is defined."""
    registration_code = 'ABCD12345678'
    url_path = '/{api_root}/registration/{code}/register/'.format(
        api_root=settings.API_ROOT,
        code=registration_code,
    )
    assert reverse('api:registration-register', kwargs={'code': registration_code}) == url_path
    assert resolve(url_path).view_name == 'api:registration-register'


def test_retrieve_caregiver_list(settings: SettingsWrapper) -> None:
    """Ensure `patients/legacy/<int:legacy_id>/caregivers/` is defined."""
    patient_id = 52
    url_path = '/{api_root}/patients/legacy/{legacy_id}/caregivers/'.format(
        api_root=settings.API_ROOT,
        legacy_id=patient_id,
    )
    assert reverse('api:caregivers-list', kwargs={'legacy_id': patient_id}) == url_path
    assert resolve(url_path).view_name == 'api:caregivers-list'


def test_patient_caregivers(settings: SettingsWrapper) -> None:
    """Ensure `patients/legacy/<int:legacy_id>/` is defined."""
    patient_id = 52
    url_path = '/{api_root}/patients/legacy/{legacy_id}/'.format(
        api_root=settings.API_ROOT,
        legacy_id=patient_id,
    )
    assert reverse('api:patient-caregivers', kwargs={'legacy_id': patient_id}) == url_path
    assert resolve(url_path).view_name == 'api:patient-caregivers'


def test_verify_email(settings: SettingsWrapper) -> None:
    """Ensure `registration/<str:code>/verify-email/` is defined."""
    registration_code = 'CODE12345678'
    url_path = '/{api_root}/registration/{code}/verify-email/'.format(
        api_root=settings.API_ROOT,
        code=registration_code,
    )
    assert reverse('api:verify-email', kwargs={'code': registration_code}) == url_path
    assert resolve(url_path).view_name == 'api:verify-email'


def test_verify_email_code(settings: SettingsWrapper) -> None:
    """Ensure `registration/<str:code>/verify-email-code/` is defined."""
    registration_code = 'CODE12345678'
    url_path = '/{api_root}/registration/{code}/verify-email-code/'.format(
        api_root=settings.API_ROOT,
        code=registration_code,
    )
    assert reverse('api:verify-email-code', kwargs={'code': registration_code}) == url_path
    assert resolve(url_path).view_name == 'api:verify-email-code'


def test_retrieve_device_update(settings: SettingsWrapper) -> None:
    """Ensure `caregivers/devices/<str:device_id>/` endpoint is defined."""
    device_id = 'TJLNf6yqHdfc3yR3C2bW6546ZPl1'
    url_path = f'/{settings.API_ROOT}/caregivers/devices/{device_id}/'
    assert reverse('api:devices-update-or-create', kwargs={'device_id': device_id}) == url_path
    assert resolve(url_path).view_name == 'api:devices-update-or-create'


def test_quantitysample_create(settings: SettingsWrapper) -> None:
    """Ensure the quantity sample endpoint is defined for a specific patient."""
    patient_id = 42
    url_path = f'/{settings.API_ROOT}/patients/{patient_id}/health-data/quantity-samples/'

    assert reverse('api:patients-data-quantity-create', kwargs={'patient_id': patient_id}) == url_path
    assert resolve(url_path).view_name == 'api:patients-data-quantity-create'


def test_api_orms_auth_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API auth endpoint for the ORMS is defined."""
    auth_login_path = '/{api_root}/auth/orms/login/'.format(api_root=settings.API_ROOT)
    assert reverse('api:orms-login') == auth_login_path
    assert resolve(auth_login_path).view_name == 'api:orms-login'


def test_patient_demographic_defined(settings: SettingsWrapper) -> None:
    """Ensure the patient demographic update endpoint is defined."""
    url_path = '/{api_root}/patients/demographic/'.format(api_root=settings.API_ROOT)
    assert reverse('api:patient-demographic-update') == url_path
    assert resolve(url_path).view_name == 'api:patient-demographic-update'
