import json
from http import HTTPStatus

from django.contrib.auth import authenticate

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError

from opal.core.test_utils import RequestMockerTest

from ..auth import AUTHENTICATION_FAILURE, AUTHENTICATION_SUCCESS, FedAuthBackend, UserData, UserModel

ENCODING = 'utf-8'

auth_backend = FedAuthBackend()


def _create_auth_data(success: str) -> dict[str, str]:
    return {
        'authenticate': success,
        'mail': 'user@example.com',
        'givenName': 'First',
        'sn': 'Last',
    }


@pytest.mark.parametrize(('success', 'expected'), [
    (AUTHENTICATION_FAILURE, None),
    (AUTHENTICATION_SUCCESS, ('user@example.com', 'First', 'Last')),
])
def test_parse_response(success: str, expected: UserData | None, mocker: MockerFixture) -> None:
    """Ensure JSON response is parsed correctly."""
    mock_logger = mocker.patch('logging.Logger.error')
    response: Response = Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(_create_auth_data(success)).encode(ENCODING)

    assert auth_backend._parse_response(response) == expected
    mock_logger.assert_not_called()


def test_parse_response_empty_response() -> None:
    """Ensure an empty JSON response does not cause an error."""
    response: Response = Response()
    response.status_code = HTTPStatus.OK
    response._content = json.dumps({}).encode(ENCODING)

    assert auth_backend._parse_response(response) is None


def test_parse_response_response_code_not_ok() -> None:
    """Ensure a non-OK status code is properly handled."""
    response: Response = Response()
    response.status_code = HTTPStatus.BAD_REQUEST

    assert auth_backend._parse_response(response) is None


def test_authenticate_fedauth(mocker: MockerFixture) -> None:
    """Ensure authenticating against fed auth returns the proper user data."""
    auth_data = _create_auth_data(AUTHENTICATION_SUCCESS)
    mock_post = RequestMockerTest.mock_requests_post(mocker, auth_data)

    user_data = auth_backend._authenticate_fedauth('user', 'pass')
    assert user_data == ('user@example.com', 'First', 'Last')

    mock_post.assert_called_once()
    post_data = mock_post.call_args.args[1]

    assert list(post_data.keys()) == ['institution', 'uid', 'pwd']


def test_authenticate_fedauth_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure authenticate uses the fed auth settings."""
    settings.FEDAUTH_API_ENDPOINT = 'http://localhost/api/login'
    settings.FEDAUTH_INSTITUTION = '99-fake-institution'

    # mock actual web API call
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = RequestsConnectionError('connection failed')

    user_data = auth_backend._authenticate_fedauth('user', 'pass')
    assert user_data is None

    mock_post.assert_called_once_with(
        'http://localhost/api/login',
        {
            'institution': '99-fake-institution',
            'uid': 'user',
            'pwd': 'pass',
        },
        timeout=10,
    )


def test_authenticate_fedauth_error(mocker: MockerFixture) -> None:
    """Ensure connection failure is handled and does not result in error."""
    # mock actual web API call to raise a connection error
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = RequestsConnectionError('connection failed')
    mock_logger = mocker.patch('logging.Logger.exception')

    user_data = auth_backend._authenticate_fedauth('user', 'pass')

    assert user_data is None
    mock_logger.assert_called_once_with('error while requesting the fed auth API')


@pytest.mark.django_db
def test_get_user() -> None:
    """Ensure get_user returns the user instance."""
    user = UserModel.objects.create(username='testuser')

    assert auth_backend.get_user(user.pk) == user


@pytest.mark.django_db
def test_get_user_does_not_exist() -> None:
    """Ensure get_user returns `None` if the user does not exist."""
    assert auth_backend.get_user(1) is None


def test_authenticate_missing_params() -> None:
    """Ensure authenticate can handle missing parameters."""
    assert auth_backend.authenticate(None, None, None) is None
    assert auth_backend.authenticate(None, 'testuser', None) is None
    assert auth_backend.authenticate(None, None, 'testpass') is None


def test_authenticate_wrong_credentials(mocker: MockerFixture) -> None:
    """Ensure authenticate returns `None` for unsuccessful authentication attempts."""
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = False

    assert auth_backend.authenticate(None, 'testuser', 'testpass') is None


@pytest.mark.django_db
def test_create_user() -> None:
    """Ensure the create_user function creates a new user."""
    user = auth_backend._create_user('johnwayne', UserData(
        'john.wayne@example.com',
        'John',
        'Wayne',
    ))

    assert UserModel.objects.count() == 1
    db_user = UserModel.objects.get()
    assert db_user == user
    assert user.username == 'johnwayne'
    assert user.email == 'john.wayne@example.com'
    assert user.first_name == 'John'
    assert user.last_name == 'Wayne'
    assert user.type == UserModel.UserType.CLINICAL_STAFF
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_authenticate_user_does_not_exist(mocker: MockerFixture) -> None:
    """Ensure authentication fails if the user does not exist."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = UserData('user@example.com', 'First', 'Last')

    user = auth_backend.authenticate(None, 'testuser', 'testpass')

    assert user is None


@pytest.mark.xfail(reason="Disabled automatic creation of user if they don't exist yet")
@pytest.mark.django_db
def test_authenticate_user_does_not_exist_new_user_created(mocker: MockerFixture) -> None:
    """Ensure a user instance is created if the user authenticates for the first time."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = UserData('user@example.com', 'First', 'Last')

    user = auth_backend.authenticate(None, 'testuser', 'testpass')
    assert user is not None
    # verify that user data was added
    assert user.email == 'user@example.com'
    assert user.first_name == 'First'
    assert user.last_name == 'Last'

    # verify that user was added
    assert UserModel.objects.get(username='testuser').pk == user.pk


@pytest.mark.xfail(reason="Disabled automatic creation of user if they don't exist yet")
@pytest.mark.django_db
def test_authenticate_new_user_clinical_staff(mocker: MockerFixture) -> None:
    """Ensure a user instance is created with the user type `CLINICAL_STAFF`."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = UserData('user@example.com', 'First', 'Last')

    user = auth_backend.authenticate(None, 'testuser', 'testpass')

    assert user is not None
    assert user.type == UserModel.UserType.CLINICAL_STAFF


@pytest.mark.xfail(reason="Disabled automatic creation of user if they don't exist yet")
@pytest.mark.django_db
def test_authenticate_new_user_unusable_password(mocker: MockerFixture) -> None:
    """Ensure a user instance is created with an unusable password."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = UserData('user@example.com', 'First', 'Last')

    user = auth_backend.authenticate(None, 'testuser', 'testpass')

    assert user is not None
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_authenticate_user_already_exists(mocker: MockerFixture) -> None:
    """Ensure the existing user instance is returned if the user already exists."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = ('user@example.com', 'First', 'Last')

    user = UserModel.objects.create(username='testuser', email='user@example.com', first_name='First', last_name='Last')

    authenticated_user = auth_backend.authenticate(None, 'testuser', 'testpass')
    assert UserModel.objects.count() == 1
    assert authenticated_user == user


@pytest.mark.django_db
def test_authenticate_user_already_exists_updated_data(mocker: MockerFixture) -> None:
    """Ensure the existing user instance is returned if the user already exists and missing data updated."""
    # mock authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = UserData('user@example.com', 'First', 'Last')

    user = UserModel.objects.create(username='testuser')

    authenticated_user = auth_backend.authenticate(None, 'testuser', 'testpass')
    assert UserModel.objects.count() == 1
    assert authenticated_user == user
    assert authenticated_user.email == 'user@example.com'
    assert authenticated_user.first_name == 'First'
    assert authenticated_user.last_name == 'Last'


@pytest.mark.xfail(reason="Disabled automatic creation of user if they don't exist yet")
@pytest.mark.django_db
def test_authenticate_integration(mocker: MockerFixture) -> None:
    """Authenticate should return new user if fed auth is successful."""
    auth_data = _create_auth_data(AUTHENTICATION_SUCCESS)
    RequestMockerTest.mock_requests_post(mocker, auth_data)

    authenticated_user = auth_backend.authenticate(None, 'testuser', 'testpass')

    assert authenticated_user is not None
    assert authenticated_user.username == 'testuser'


@pytest.mark.xfail(reason="Disabled automatic creation of user if they don't exist yet")
@pytest.mark.django_db
def test_authenticate_integration_incomplete_data(mocker: MockerFixture) -> None:
    """A missing email in the response should still authenticate the user."""
    # assume incomplete data is returned
    auth_data = {
        'authenticate': AUTHENTICATION_SUCCESS,
        'givenName': 'Hans',
        'sn': 'Wurst',
    }
    RequestMockerTest.mock_requests_post(mocker, auth_data)

    authenticated_user = auth_backend.authenticate(None, 'testuser', 'testpass')

    assert authenticated_user is not None
    assert authenticated_user.username == 'testuser'


@pytest.mark.django_db
def test_django_authentication_integration(mocker: MockerFixture) -> None:
    """Django authenticate should return user on successful authentication using fed auth."""
    user = UserModel.objects.create(username='testuser')

    # assume incomplete data is returned
    auth_data = _create_auth_data(AUTHENTICATION_SUCCESS)
    RequestMockerTest.mock_requests_post(mocker, auth_data)
    # spy on FedAuthBackend.authenticate to ensure it was called
    mock_fedauth = mocker.spy(FedAuthBackend, 'authenticate')

    authenticated_user = authenticate(None, username='testuser', password='testpass')

    assert authenticated_user == user
    mock_fedauth.assert_called()
