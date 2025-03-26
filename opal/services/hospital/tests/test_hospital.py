import json
from datetime import datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import requests
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture

from opal.services.hospital.hospital import OIEMRNData, OIEPatientData, OIEReportExportData, OIEService
from opal.services.hospital.hospital_communication import OIEHTTPCommunicationManager
from opal.services.hospital.hospital_error import OIEErrorHandler
from opal.services.hospital.hospital_validation import OIEValidator

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
RAMQ_VALID = 'ABCD12345678'
RAMQ_INVALID = 'ABC123456789'
MRN = '9999996'
SITE_CODE = 'MUHC'
OIE_CREDENTIALS_USER = 'questionnaire'
OIE_CREDENTIALS = '12345Opal!!'
OIE_HOST = 'https://localhost'

OIE_PATIENT_DATA = dict({
    'dateOfBirth': '1953-01-01 00:00:00',
    'firstName': 'SANDRA',
    'lastName': 'TESTMUSEMGHPROD',
    'sex': 'F',
    'alias': '',
    'deceased': True,
    'deathDateTime': '2023-01-01 00:00:00',
    'ramq': 'TESS53510111',
    'ramqExpiration': '2018-01-31 23:59:59',
    'mrns': [
        {
            'site': 'MGH',
            'mrn': '9999993',
            'active': True,
        },
    ],
})

oie_service = OIEService()


def _create_report_export_response_data() -> dict[str, str]:
    """Create mock `dict` response on the `report export` HTTP POST request.

    Returns:
        dict[str, str]: mock data response
    """
    return {'status': 'success'}


def _mock_requests_post(
    mocker: MockerFixture,
    response_data: dict[str, Any],
) -> MagicMock:
    """Mock actual HTTP POST web API call to the OIE.

    Args:
        mocker (MockerFixture): object that provides the same interface to functions in the mock module
        response_data (dict[str, str]): generated mock response data

    Returns:
        MagicMock: object that mocks HTTP post request to the OIE requests
    """
    mock_post = mocker.patch('requests.post')
    response = requests.Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(response_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


# __init__

def test_init_types() -> None:
    """Ensure init function creates helper services of certain types."""
    assert isinstance(oie_service.communication_manager, OIEHTTPCommunicationManager)
    assert isinstance(oie_service.error_handler, OIEErrorHandler)
    assert isinstance(oie_service.validator, OIEValidator)


def test_init_not_none() -> None:
    """Ensure init function creates helper services that are not `None`."""
    assert oie_service.communication_manager is not None
    assert oie_service.error_handler is not None
    assert oie_service.validator is not None


# export_pdf_report

def test_export_pdf_report(mocker: MockerFixture) -> None:
    """Ensure successful report export request returns json response with successful HTTP status."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert report_data['status'] == 'success'

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['json'])

    assert list(post_data.keys()) == ['mrn', 'site', 'reportContent', 'docType', 'documentDate']


def test_export_pdf_report_error(mocker: MockerFixture) -> None:
    """Ensure export request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
        },
    }
    _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
        },
    }


def test_export_pdf_report_response_invalid(mocker: MockerFixture) -> None:
    """Ensure invalid response is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'invalidStatus': 'error',
    }
    _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
            'responseData': {
                'invalidStatus': 'error',
            },
        },
    }


def test_export_pdf_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Expecting value: line 1 column 1 (char 0)'


def test_export_pdf_report_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure OIE export report request uses report settings."""
    settings.OIE_USER = OIE_CREDENTIALS_USER
    settings.OIE_PASSWORD = OIE_CREDENTIALS
    settings.OIE_HOST = OIE_HOST

    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data['status'] == 'success'

    payload = json.dumps({
        'mrn': MRN,
        'site': SITE_CODE,
        'reportContent': BASE64_ENCODED_REPORT,
        'docType': DOCUMENT_NUMBER,
        'documentDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    # assert that the mock was called exactly once and that the call was with exactly the same
    # parameters as in the `export_pdf_report` post request.
    # Arguments: *args, **kwargs
    mock_post.assert_called_once_with(
        url='{0}{1}'.format(OIE_HOST, '/report/post'),
        auth=requests.auth.HTTPBasicAuth(OIE_CREDENTIALS_USER, OIE_CREDENTIALS),
        headers=None,
        json=payload,
        timeout=5,
    )


def test_export_pdf_report_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid MRN is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn='',
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_site(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid site is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)

    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site='',
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_base64(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid base64 content is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content='',
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_doc_type(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid document type is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number='invalid document type',
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was successful
    _mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d %H:%M:%S',
        ),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=datetime.strptime(
            str(OIE_PATIENT_DATA['deathDateTime']),
            '%Y-%m-%d %H:%M:%S',
        ),
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=datetime.strptime(
            str(OIE_PATIENT_DATA['ramqExpiration']),
            '%Y-%m-%d %H:%M:%S',
        ),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_empty_value_in_response_by_mrn(mocker: MockerFixture) -> None:
    """Ensure that None value in response returned from find_patient_by_mrn."""
    oie_patient_data_copy = OIE_PATIENT_DATA.copy()
    oie_patient_data_copy.update(deathDateTime='', ramqExpiration='')
    # mock find_patient_by_mrn and pretend it was successful
    _mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': oie_patient_data_copy,
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d %H:%M:%S',
        ),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=None,
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=None,
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_find_patient_by_mrn_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return None."""
    # mock find_patient_by_mrn and pretend it was failed
    _mock_requests_post(
        mocker,
        {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
            },
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'error'
    assert response['data'] == {
        'message': ['Could not establish a connection to the hospital interface.', 'Caused by ConnectTimeoutError.'],
        'responseData': {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
            },
        },
    }


def test_find_patient_by_mrn_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_mrn request with invalid MRN is handled and does not result in an error."""
    response = oie_service.find_patient_by_mrn('', SITE_CODE)
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided MRN or site is invalid.'


def test_find_patient_by_mrn_invalid_site(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_mrn request with invalid site is handled and does not result in an error."""
    response = oie_service.find_patient_by_mrn(MRN, '')
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided MRN or site is invalid.'


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return the expected OIE data structure."""
    # mock find_patient_by_ramq and pretend it was successful
    _mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d %H:%M:%S',
        ),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=datetime.strptime(
            str(OIE_PATIENT_DATA['deathDateTime']),
            '%Y-%m-%d %H:%M:%S',
        ),
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=datetime.strptime(
            str(OIE_PATIENT_DATA['ramqExpiration']),
            '%Y-%m-%d %H:%M:%S',
        ),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_empty_value_in_response_by_ramq(mocker: MockerFixture) -> None:
    """Ensure that None value in response returned from find_patient_by_ramq."""
    oie_patient_data_copy = OIE_PATIENT_DATA.copy()
    oie_patient_data_copy.update(deathDateTime='', ramqExpiration='')
    # mock find_patient_by_ramq and pretend it was successful
    _mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': oie_patient_data_copy,
        },
    )

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d %H:%M:%S',
        ),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=None,
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=None,
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_find_patient_by_ramq_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return None."""
    # mock find_patient_by_mrn and pretend it was failed
    _mock_requests_post(
        mocker,
        {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
            },
        },
    )

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)
    assert response['status'] == 'error'
    assert response['data'] == {
        'message': ['Could not establish a connection to the hospital interface.', 'Caused by ConnectTimeoutError.'],
        'responseData': {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
            },
        },
    }


def test_find_patient_by_ramq_invalid_ramq(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_ramq request with invalid ramq is handled and does not result in an error."""
    # mock find_patient_by_mrn and pretend it was failed
    _mock_requests_post(mocker, {'status': 'success'})

    response = oie_service.find_patient_by_ramq(RAMQ_INVALID)
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided RAMQ is invalid.'
