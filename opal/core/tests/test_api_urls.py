import sys
from importlib import reload
from urllib.parse import unquote

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
    """Ensure that the REST API app chart endpoints are defined."""
    app_chart_path = '/{api_root}/app/chart/'.format(api_root=settings.API_ROOT)
    assert reverse('api:app-chart') == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:app-chart'


def test_api_security_questions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API security questions endpoints are defined."""
    app_chart_path = '/{api_root}/security-questions/'.format(api_root=settings.API_ROOT)
    assert reverse('api:security-questions') == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:security-questions'


def test_api_random_security_question_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions random endpoints are defined."""
    app_chart_path = '/{api_root}/caregivers/security-questions/random/'.format(api_root=settings.API_ROOT)
    assert reverse('api:random-question') == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:random-question'


def test_api_carigiver_security_questions_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions are defined."""
    app_chart_path = '/{api_root}/caregivers/security-questions/'.format(api_root=settings.API_ROOT)
    assert reverse('api:update-question') == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:update-question'


def test_api_verify_secruity_answer_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API carigiver security questions verify endpoints are defined."""
    app_chart_path = '/{api_root}/caregivers/security-questions/<question_id>/verify'.format(api_root=settings.API_ROOT)
    assert unquote(reverse('api:verify-answer', kwargs={'question_id': '<question_id>'})) == app_chart_path
    assert resolve(app_chart_path).view_name == 'api:verify-answer'
