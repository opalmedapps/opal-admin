import json
from http import HTTPStatus
from unittest.mock import MagicMock

import requests
from pytest_mock.plugin import MockerFixture

from opal.services.hospital.hospital_communication import OIEHTTPCommunicationManager
from opal.services.hospital.hospital_error import OIEErrorHandler

ENCODING = 'utf-8'

communication_manager = OIEHTTPCommunicationManager()


def _create_response_data() -> dict[str, str]:
    """Create mock `dict` response on the HTTP POST request.

    Returns:
        dict[str, str]: mock data response
    """
    return {'status': 'success'}


def _mock_requests_post(
    mocker: MockerFixture,
    generated_response_data: dict[str, str],
) -> MagicMock:
    """Mock actual HTTP POST web API call to the OIE.

    Args:
        mocker (MockerFixture): object that provides the same interface to functions in the mock module
        generated_response_data (dict[str, str]): generated mock response data

    Returns:
        MagicMock: object that mocks HTTP post request to the OIE for exporting reports
    """
    mock_post = mocker.patch('requests.post')
    response = requests.Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_response_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


def _mock_requests_get(
    mocker: MockerFixture,
    generated_response_data: dict[str, str],
) -> MagicMock:
    """Mock actual HTTP GET web API call to the OIE.

    Args:
        mocker (MockerFixture): object that provides the same interface to functions in the mock module
        generated_response_data (dict[str, str]): generated mock response data

    Returns:
        MagicMock: object that mocks HTTP get request to the OIE for exporting reports
    """
    mock_get = mocker.patch('requests.get')
    response = requests.Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_response_data).encode(ENCODING)
    mock_get.return_value = response

    return mock_get


# __init__

def test_init() -> None:
    """Ensure init function creates error handler (a.k.a., error helper service)."""
    assert isinstance(communication_manager.error_handler, OIEErrorHandler)
    assert communication_manager.error_handler is not None


# submit

def test_submit_success(mocker: MockerFixture) -> None:
    """Ensure successful submit request returns json response with successful HTTP status."""
    # mock actual OIE API call
    generated_data = _create_response_data()
    mock_post = _mock_requests_post(mocker, generated_data)

    response_data = communication_manager.submit(
        endpoint='/test/endpoint',
        payload={},
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_data['status'] == 'success'

    mock_post.assert_called_once()


def test_submit_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_data = _create_response_data()
    mock_post = _mock_requests_post(mocker, generated_data)
    mock_post.side_effect = requests.RequestException('request failed')
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    response_data = communication_manager.submit(
        endpoint='/test/endpoint',
        payload={},
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert response_data == {
        'status': 'error',
        'data': {
            'message': 'request failed',
        },
    }


def test_submit_invalid_payload(mocker: MockerFixture) -> None:
    """Ensure invalid payload is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_post = _mock_requests_post(mocker, error_response)

    response_data = communication_manager.submit(
        endpoint='/test/endpoint',
        payload=123,  # type: ignore[arg-type]
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_submit_invalid_port(mocker: MockerFixture) -> None:
    """Ensure invalid port is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_post = _mock_requests_post(mocker, error_response)

    response_data = communication_manager.submit(
        endpoint=':-1/test/endpoint',
        payload={},
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_submit_invalid_metadata(mocker: MockerFixture) -> None:
    """Ensure invalid metadata are handled and do not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_post = _mock_requests_post(mocker, error_response)

    response_data = communication_manager.submit(
        endpoint='/test/endpoint',
        payload={},
        metadata=123,  # type: ignore[arg-type]
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_submit_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = 'invalid json'
    mock_post = _mock_requests_post(mocker, error_response)  # type: ignore[arg-type]
    mock_post.side_effect = requests.exceptions.JSONDecodeError(
        'request failed',
        error_response,
        0,
    )
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    response_data = communication_manager.submit(
        endpoint='/test/endpoint',
        payload={},
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert response_data == {
        'status': 'error',
        'data': {
            'message': 'request failed: line 1 column 1 (char 0)',
        },
    }


# fetch

def test_fetch_success(mocker: MockerFixture) -> None:
    """Ensure successful fetch request returns json response with successful HTTP status."""
    # mock actual OIE API call
    generated_data = _create_response_data()
    mock_get = _mock_requests_get(mocker, generated_data)

    response_data = communication_manager.fetch(
        endpoint='/test/endpoint',
        params={'param1': 'value1', 'param2': 'value2'},
    )

    assert mock_get.return_value.status_code == HTTPStatus.OK
    assert response_data['status'] == 'success'

    mock_get.assert_called_once()


def test_fetch_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_data = _create_response_data()
    mock_get = _mock_requests_get(mocker, generated_data)
    mock_get.side_effect = requests.RequestException('request failed')
    mock_get.return_value.status_code = HTTPStatus.BAD_REQUEST

    response_data = communication_manager.fetch(
        endpoint='/test/endpoint',
    )

    assert mock_get.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert response_data == {
        'status': 'error',
        'data': {
            'message': 'request failed',
        },
    }


def test_fetch_invalid_parameters(mocker: MockerFixture) -> None:
    """Ensure invalid parameters are handled and do not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_get = _mock_requests_get(mocker, error_response)

    response_data = communication_manager.fetch(
        endpoint='/test/endpoint',
        params='invalid params',  # type: ignore[arg-type]
    )

    assert mock_get.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_fetch_invalid_port(mocker: MockerFixture) -> None:
    """Ensure invalid port is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_get = _mock_requests_get(mocker, error_response)

    response_data = communication_manager.fetch(
        endpoint=':-1/test/endpoint',
    )

    assert mock_get.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_fetch_invalid_metadata(mocker: MockerFixture) -> None:
    """Ensure invalid metadata are handled and do not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = {'message': 'request failed'}
    mock_get = _mock_requests_get(mocker, error_response)

    response_data = communication_manager.fetch(
        endpoint='/test/endpoint',
        metadata=123,  # type: ignore[arg-type]
    )

    assert mock_get.return_value.status_code == HTTPStatus.OK
    assert response_data == {
        'message': 'request failed',
    }


def test_fetch_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    error_response = 'invalid json response'
    mock_get = _mock_requests_get(mocker, error_response)  # type: ignore[arg-type]
    mock_get.side_effect = requests.exceptions.JSONDecodeError(
        'request failed',
        error_response,
        0,
    )
    mock_get.return_value.status_code = HTTPStatus.BAD_REQUEST

    response_data = communication_manager.fetch(
        endpoint='/test/endpoint',
        params={},
    )

    assert mock_get.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert response_data == {
        'status': 'error',
        'data': {
            'message': 'request failed: line 1 column 1 (char 0)',
        },
    }
