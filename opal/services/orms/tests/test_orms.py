import uuid

from pytest_mock.plugin import MockerFixture

from opal.core.test_utils import RequestMockerTest
from opal.services.general.service_error import ServiceErrorHandler
from opal.services.orms.orms import ORMSService
from opal.services.orms.orms_communication import ORMSHTTPCommunicationManager
from opal.services.orms.orms_validation import ORMSValidator

orms_service = ORMSService()


def test_init_types() -> None:
    """Ensure init function creates helper services of certain types."""
    assert isinstance(orms_service.communication_manager, ORMSHTTPCommunicationManager)
    assert isinstance(orms_service.error_handler, ServiceErrorHandler)
    assert isinstance(orms_service.validator, ORMSValidator)


def test_init_not_none() -> None:
    """Ensure init function creates helper services that are not `None`."""
    assert orms_service.communication_manager is not None
    assert orms_service.error_handler is not None
    assert orms_service.validator is not None


def test_set_opal_patient_success(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient can succeed."""
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'Success',
        },
    )

    response = orms_service.set_opal_patient(
        [
            ('RVH', '0000001'),
            ('MCH', '0000002'),
        ],
        uuid.uuid4(),
    )

    assert response['status'] == 'success'
    assert not hasattr(response, 'data')


def test_set_opal_patient_empty_input(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient fails gracefully when given an empty MRN list."""
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'Success',
        },
    )

    response = orms_service.set_opal_patient([], uuid.uuid4())

    assert response['status'] == 'error'
    assert 'A list of active (site, mrn) tuples should be provided' in response['data']['message']


def test_set_opal_patient(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient returns an error for invalid input."""
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'Error',
            'error': 'Some error message',
        },
    )

    response = orms_service.set_opal_patient(
        [
            ('RVH', '0000001'),
            ('MCH', '0000002'),
        ],
        uuid.uuid4(),
    )

    assert response['status'] == 'error'
    assert response['data']['responseData']['error'] == 'Some error message'
