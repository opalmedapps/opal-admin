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


def test_api_check_permissions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API check_permissions endpoint is defined."""
    check_permissions_path = '/{api_root}/patients/legacy/{legacy_id}/check_permissions/'.format(
        api_root=settings.API_ROOT,
        legacy_id=1,
    )
    assert reverse('api:caregiver-permissions', kwargs={'legacy_id': 1}) == check_permissions_path
    assert resolve(check_permissions_path).view_name == 'api:caregiver-permissions'


# questionnaire report generation API endpoint: questionnaires/reviewed/

def test_questionnaires_reviewed() -> None:
    """Ensure `questionnaires/reviewed/` endpoint is defined."""
    assert reverse('api:questionnaires-reviewed') == '/api/questionnaires/reviewed/'
    assert resolve('/api/questionnaires/reviewed/').view_name == 'api:questionnaires-reviewed'


def test_retrieve_registration_code() -> None:
    """Ensure `registration/<str:code>/` endpoint is defined."""
    assert reverse('api:registration-code', kwargs={'code': 'ABCD12345678'}) == '/api/registration/ABCD12345678/'
    assert resolve('/api/registration/ABCD12345678/').view_name == 'api:registration-code'
