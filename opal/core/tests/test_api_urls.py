from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch, Resolver404

import pytest
from pytest_django.fixtures import SettingsWrapper


# note: cannot test the opposite (APIRootView defined in debug mode)
# since the first test loads the URLs and the router is defined at that time
def test_api_root_debug_only(settings: SettingsWrapper) -> None:
    """Ensure that the API root is not available when not in debug mode."""
    assert settings.DEBUG is False

    path = '/{api_root}/'.format(api_root=settings.API_ROOT)
    with pytest.raises(NoReverseMatch):
        reverse('api:api-root')
    with pytest.raises(Resolver404):
        resolve(path)


def test_api_auth_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API auth endpoints are defined."""
    auth_login_path = '/{api_root}/auth/login/'.format(api_root=settings.API_ROOT)
    assert reverse('api:rest_login') == auth_login_path
    assert resolve(auth_login_path).view_name == 'api:rest_login'
