# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, datetime
from http import HTTPStatus
from pathlib import Path

from django.utils import timezone

import pytest
from fpdf import FPDFException
from pytest_mock.plugin import MockerFixture

from opal.services.reports import questionnaire
from opal.services.reports.base import InstitutionData, PatientData

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
ENCODING = 'utf-8'
LOGO_PATH = Path('opal/tests/fixtures/test_logo.png')
NON_STRING_VALUE = 123
TEST_LEGACY_QUESTIONNAIRES_REPORT_URL = 'http://localhost:80/report'

QUESTION_REPORT_DATA = (
    questionnaire.Question(
        question_text='Question demo',
        question_label='demo',
        question_type_id=questionnaire.QuestionType.TEXT,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'Demo answer',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question demo',
        question_label='demo',
        question_type_id=questionnaire.QuestionType.CHECKBOX,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                'Demo answer',
            ),
        ],
    ),
)
QUESTION_REPORT_DATA_CHARTS = (
    questionnaire.Question(
        question_text='Question charts demo',
        question_label='charts demo',
        question_type_id=questionnaire.QuestionType.NUMERIC,
        position=1,
        min_value=5,
        max_value=7,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
)
QUESTION_REPORT_DATA_MULTIPLE_CHARTS = (
    questionnaire.Question(
        question_text='Question charts demo',
        question_label='charts demo1',
        question_type_id=questionnaire.QuestionType.NUMERIC,
        position=1,
        min_value=5,
        max_value=7,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question text demo',
        question_label='text demo',
        question_type_id=questionnaire.QuestionType.TEXT,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                'data',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question charts after break, no max and min',
        question_label='break demo',
        question_type_id=questionnaire.QuestionType.NUMERIC,
        position=1,
        min_value=None,
        max_value=None,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question charts demo',
        question_label='charts demo',
        question_type_id=questionnaire.QuestionType.NUMERIC,
        position=1,
        min_value=5,
        max_value=7,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question radio before break',
        question_label='text demo',
        question_type_id=questionnaire.QuestionType.RADIO,
        position=1,
        min_value=5,
        max_value=7,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
    questionnaire.Question(
        question_text='Question checkbox after break',
        question_label='text demo',
        question_type_id=questionnaire.QuestionType.CHECKBOX,
        position=1,
        min_value=5,
        max_value=7,
        polarity=0,
        section_id=1,
        answers=[
            (
                datetime(2024, 10, 20, 14, 0, tzinfo=timezone.get_current_timezone()),
                '5',
            ),
            (
                datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
                '7',
            ),
        ],
    ),
)
QUESTIONNAIRE_REPORT_DATA_SHORT_NICKNAME = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='BREAST-Q Reconstruction Module',
    last_updated=datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
    questions=list(QUESTION_REPORT_DATA),
)
QUESTIONNAIRE_REPORT_DATA_LONG_NICKNAME = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='Revised Version Edmonton Symptom Assessment System (ESAS-r)',
    last_updated=datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
    questions=list(QUESTION_REPORT_DATA),
)
QUESTIONNAIRE_REPORT_DATA_WITH_CHARTS = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='Questionnaire demo with charts for questions',
    last_updated=datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
    questions=list(QUESTION_REPORT_DATA_CHARTS),
)
QUESTIONNAIRE_REPORT_DATA_WITH_MULTIPLE_CHARTS = questionnaire.QuestionnaireData(
    questionnaire_id=1,
    questionnaire_title='Questionnaire demo with charts for questions',
    last_updated=datetime(2024, 10, 21, 14, 0, tzinfo=timezone.get_current_timezone()),
    questions=list(QUESTION_REPORT_DATA_MULTIPLE_CHARTS),
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
    document_number='FMU-8624',
    source_system='OPAL',
)


def _create_generated_report_data(status: HTTPStatus) -> dict[str, dict[str, str]]:
    """
    Create mock `dict` response on the `report` HTTP POST request.

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


# Marking this slow since the test uses chromium
@pytest.mark.slow
# Allow hosts to make the test work for Windows, Linux and Unix-based environements
@pytest.mark.allow_hosts(['127.0.0.1'])
def test_generate_pdf_charts() -> None:
    """Ensure that the PDF is correctly generated."""
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


# Marking this slow since the test uses chromium
@pytest.mark.slow
# Allow hosts to make the test work for Windows, Linux and Unix-based  environements
@pytest.mark.allow_hosts(['127.0.0.1'])
def test_draw_text_answer_and_charts_question_page_break(mocker: MockerFixture) -> None:
    """Ensure that the page break is correctly handled while drawing charts and tables."""
    add_page = mocker.spy(
        questionnaire.QuestionnairePDF,
        'add_page',
    )
    draw_text_answer = mocker.spy(
        questionnaire.QuestionnairePDF,
        '_draw_text_answer_question',
    )

    prepare_chart = mocker.spy(
        questionnaire.QuestionnairePDF,
        '_prepare_question_chart',
    )
    will_page_break = mocker.spy(
        questionnaire.QuestionnairePDF,
        'will_page_break',
    )
    questionnaire.generate_pdf(
        INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        [QUESTIONNAIRE_REPORT_DATA_WITH_MULTIPLE_CHARTS],
    )

    pdf_instance = will_page_break.call_args[0][0]

    count_page_break_charts = sum(1 for call in will_page_break.call_args_list if call.args == (pdf_instance, 50))
    count_page_break_text = sum(1 for call in will_page_break.call_args_list if call.args == (pdf_instance, 30))
    assert count_page_break_charts == 3
    assert count_page_break_text == 3

    assert prepare_chart.call_count == 3
    assert draw_text_answer.call_count == 3
    assert add_page.call_count == 6
