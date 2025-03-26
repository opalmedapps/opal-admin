import json
from datetime import date, datetime
from http import HTTPStatus
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture  # noqa: WPS436
from fpdf import FPDFException
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests.exceptions import RequestException

from opal.core.test_utils import RequestMockerTest
from opal.patients import factories as patient_factories
from opal.services.reports import questionnaire
from opal.services.reports.base import InstitutionData, PatientData
from opal.utils.base64_util import Base64Util

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
ENCODING = 'utf-8'
LOGO_PATH = Path('opal/tests/fixtures/test_logo.png')
NON_STRING_VALUE = 123
TEST_LEGACY_QUESTIONNAIRES_REPORT_URL = 'http://localhost:80/report'

report_service = questionnaire.ReportService()

QUESTIONNAIRE_REPORT_REQUEST_DATA = questionnaire.QuestionnaireReportRequestData(
    patient_id=51,
    patient_name='Bart Simpson',
    patient_site='RVH',
    patient_mrn='9999996',
    logo_path=LOGO_PATH,
    language='en',
)


QUESTION_REPORT_DATA = (
    questionnaire.Question(
        question_text='Question demo for patient 1',
        question_label='demo for patient',
        question_type_id=1,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        values=[
            (
                datetime(2024, 10, 20, 14, 0),
                'Demo answer from patient 1',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question demo for patient 2',
        question_label='demo for patient',
        question_type_id=1,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        values=[
            (
                datetime(2024, 10, 21, 14, 0),
                'Demo answer from patient 2',
            ),
        ],
    ),
)
QUESTION_REPORT_DATA_CHARTS = (
    questionnaire.Question(
        question_text='Question charts demo for patient',
        question_label='charts demo',
        question_type_id=2,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        values=[
            (
                datetime(2024, 10, 20, 14, 0),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0),
                '7',
            ),
        ],
    ),
)

QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='BREAST-Q Reconstruction Module',
    last_updated=datetime(2024, 10, 21, 14, 0),
    questions=list(QUESTION_REPORT_DATA),
)
QUESTIONNAIRE_REPORT_DATA_LONG_NICKNAME = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='Revised Version Edmonton Symptom Assessment System (ESAS-r)',
    last_updated=datetime(2024, 10, 21, 14, 0),
    questions=list(QUESTION_REPORT_DATA),
)
QUESTIONNAIRE_REPORT_DATA_WITH_CHARTS = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='Questionnaire demo with charts for questions',
    last_updated=datetime(2024, 10, 21, 14, 0),
    questions=list(QUESTION_REPORT_DATA_CHARTS),
)

PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK = PatientData(
    patient_first_name='Bart',
    patient_last_name='Simpson',
    patient_date_of_birth=date(1999, 1, 1),
    patient_ramq='SIMM99999999',
    patient_sites_and_mrns=[
        {'mrn': '22222443', 'site_code': 'MGH'},
        {'mrn': '1111728', 'site_code': 'RVH'},
    ],
)
INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK = InstitutionData(
    institution_logo_path=Path('opal/tests/fixtures/test_logo.png'),
)


def _create_generated_report_data(status: HTTPStatus) -> dict[str, dict[str, str]]:
    """Create mock `dict` response on the `report` HTTP POST request.

    Args:
        status: response status code

    Returns:
        mock data response
    """
    return {
        'data': {
            'status': f'Success: {status}',
            'base64EncodedReport': BASE64_ENCODED_REPORT,
        },
    }


# _is_questionnaire_report_request_data_valid

def test_is_questionnaire_report_data_valid() -> None:
    """Ensure `QuestionnaireReportRequestData` successfully validates."""
    assert report_service._is_questionnaire_report_request_data_valid(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )


def test_is_questionnaire_report_invalid_patient() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid patient) are handled and does not result in an error."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        patient_id=-1,
    )

    assert report_service._is_questionnaire_report_request_data_valid(report_data) is False


def test_is_questionnaire_report_invalid_logo() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid logo) are handled and does not result in an error."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        logo_path=Path('invalid/logo/path'),
    )

    assert report_service._is_questionnaire_report_request_data_valid(report_data) is False


def test_is_questionnaire_report_invalid_language() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid language) are handled without errors."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        language='invalid_language',
    )

    assert report_service._is_questionnaire_report_request_data_valid(report_data) is False


# _request_base64_report function tests

def test_request_base64_report(mocker: MockerFixture) -> None:
    """Ensure successful report request returns base64 encoded PDF report."""
    patient_factories.HospitalPatient(
        site=patient_factories.Site(acronym='RVH'),
    )
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    response_base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_base64_report == BASE64_ENCODED_REPORT

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['data'])

    assert list(post_data.keys()) == [
        'patient_id',
        'patient_name',
        'patient_site',
        'patient_mrn',
        'logo_base64',
        'language',
    ]


def test_request_base64_report_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.side_effect = RequestException('request failed')

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_bad_request(mocker: MockerFixture) -> None:
    """Ensure request failure (bad request response) is handled and does not result in an error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(HTTPStatus.BAD_REQUEST)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert base64_report is None


def test_request_base64_report_json_key_error(mocker: MockerFixture) -> None:
    """Ensure response json key failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = json.dumps({}).encode(ENCODING)

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_is_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport value is a string."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert isinstance(base64_report, str)


def test_request_base64_report_not_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport non-string value is handled and does not result in an error."""
    patient_factories.HospitalPatient(
        site=patient_factories.Site(acronym='RVH'),
    )
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    data = _create_generated_report_data(HTTPStatus.OK)
    data['data']['base64EncodedReport'] = NON_STRING_VALUE  # type: ignore[assignment]
    mock_post.return_value._content = json.dumps(data).encode(ENCODING)

    base64_report = report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure base64 report request uses report settings."""
    settings.LEGACY_QUESTIONNAIRES_REPORT_URL = TEST_LEGACY_QUESTIONNAIRES_REPORT_URL

    # mock actual web API call
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.OK

    report_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK

    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({
        'patient_id': 51,
        'patient_name': 'Bart Simpson',
        'patient_site': 'RVH',
        'patient_mrn': '9999996',
        'logo_base64': Base64Util().encode_to_base64(LOGO_PATH),
        'language': 'en',
    })
    mock_post.assert_called_once_with(
        url=TEST_LEGACY_QUESTIONNAIRES_REPORT_URL,
        headers=headers,
        data=payload,
        timeout=60,
    )


# generate_base64_questionnaire_report function tests

def test_questionnaire_report(mocker: MockerFixture) -> None:
    """Ensure the returned value is base64 encoded PDF report."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert Base64Util().is_base64(base64_report)
    assert base64_report == BASE64_ENCODED_REPORT


def test_questionnaire_report_error(mocker: MockerFixture) -> None:
    """Ensure function failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.BAD_REQUEST)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            patient_id=-1,
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert base64_report is None


def test_questionnaire_report_invalid_patient(mocker: MockerFixture) -> None:
    """Ensure invalid patient id is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            patient_id=-1,
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_invalid_logo(mocker: MockerFixture) -> None:
    """Ensure invalid logo path is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            logo_path=Path('invalid/logo/path'),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_invalid_language(mocker: MockerFixture) -> None:
    """Ensure invalid language is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            language='invalid language',
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_no_base64(mocker: MockerFixture, caplog: LogCaptureFixture) -> None:
    """Ensure that when the report is not base64 an error is logged."""
    mock_post = RequestMockerTest.mock_requests_post(mocker, {
        'data': {
            'status': f'Success: {HTTPStatus.OK}',
            'base64EncodedReport': 'not-base64',
        },
    })

    base64_report = report_service.generate_base64_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None

    assert caplog.records[0].message == 'The generated questionnaire PDF report is not in the base64 format.'
    assert caplog.records[0].levelname == 'ERROR'


# TODO: add test for pdf generation with charts once it is in the container


def test_generate_pdf_one_page() -> None:
    """Ensure that the pdf is correctly generated."""
    pdf_bytes = questionnaire.generate_pdf(
        INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        [QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME],
    )
    content = pdf_bytes.decode('latin1')
    page_count = content.count('/Type /Page\n')

    assert page_count == 2, 'PDF should have the expected amount of pages'
    assert isinstance(pdf_bytes, bytearray), 'Output'
    assert pdf_bytes, 'PDF should not be empty'


def test_generate_pdf_charts() -> None:
    """Ensure that the pdf is correctly generated."""
    pdf_bytes = questionnaire.generate_pdf(
        INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        [QUESTIONNAIRE_REPORT_DATA_WITH_CHARTS],
    )
    content = pdf_bytes.decode('latin1')
    page_count = content.count('/Type /Page\n')

    assert page_count == 2, 'PDF should have the expected amount of pages'
    assert isinstance(pdf_bytes, bytearray), 'Output'
    assert pdf_bytes, 'PDF should not be empty'


def test_generate_pdf_multiple_pages() -> None:
    """Ensure that the pdf is correctly generated with the toc being multiple pages."""
    questionnaire_data = [QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME for _ in range(17)]

    pdf_bytes = questionnaire.generate_pdf(
        INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        questionnaire_data,
    )
    content = pdf_bytes.decode('latin1')
    page_count = content.count('/Type /Page\n')

    assert page_count == 19, 'PDF should have the expected amount of pages'
    assert isinstance(pdf_bytes, bytearray), 'Output'
    assert pdf_bytes, 'PDF should not be empty'


def test_generate_pdf_multiple_pages_with_long_name(mocker: MockerFixture) -> None:
    """
    Ensure that the pdf is correctly generated with the toc being multiple pages.

    Make sure the calculation fails and _generate_pdf gets called a second time to retrieves
    the right number of pages for the TOC.
    """
    mock_generate = mocker.spy(questionnaire, '_generate_pdf')
    # 14 with short name fit on one ToC page
    # create 13 with short names and one with long name to cause the ToC to span 2 pages
    data = [QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME for _ in range(13)] + [QUESTIONNAIRE_REPORT_DATA_LONG_NICKNAME]
    institution_data = INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK
    patient_data = PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK

    pdf_bytes = questionnaire.generate_pdf(
        institution_data,
        patient_data,
        data,
    )

    content = pdf_bytes.decode('latin1')
    page_count = content.count('/Type /Page\n')

    assert page_count == 16, 'PDF should have the expected amount of pages'
    assert isinstance(pdf_bytes, bytearray), 'Output'
    assert pdf_bytes, 'PDF should not be empty'
    mock_generate.assert_has_calls([
        mocker.call(institution_data, patient_data, data),
        mocker.call(institution_data, patient_data, data, 2),
    ])


def test_generate_pdf_empty_list() -> None:
    """Ensure that the pdf is correctly generated with an empty list."""
    questionnaire_data: list[questionnaire.QuestionnaireData] = []

    pdf_bytes = questionnaire.generate_pdf(
        INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        questionnaire_data,
    )
    assert isinstance(pdf_bytes, bytearray), 'Output'
    assert pdf_bytes, 'PDF should not be empty'


def test_generate_pdf_no_toc_error(mocker: MockerFixture) -> None:
    """Ensure PDF generation raises the exception if ToC error is missing."""
    institution_data = INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK
    patient_data = PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK
    questionnaire_data = [QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME]

    mocker.patch(
        'opal.services.reports.questionnaire._generate_pdf',
        side_effect=FPDFException('Some other error'),
    )
    with pytest.raises(FPDFException) as excinfo:
        questionnaire.generate_pdf(institution_data, patient_data, questionnaire_data)

    assert 'Some other error' in str(excinfo.value)


def test_generate_pdf_toc_regex_no_match(mocker: MockerFixture) -> None:
    """Ensure PDF generation does not proceed when regex doesn't match."""
    institution_data = INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK
    patient_data = PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK
    questionnaire_data = [QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME]

    mocker.patch(
        'opal.services.reports.questionnaire._generate_pdf',
        side_effect=FPDFException(
            'ToC ended on page 10 while expected to span more pages',
        ),
    )
    with pytest.raises(FPDFException) as excinfo:
        questionnaire.generate_pdf(institution_data, patient_data, questionnaire_data)

    error_message = str(excinfo.value)
    assert 'ToC ended on page' in error_message
