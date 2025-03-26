import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import CommandError
from django.utils import timezone

import pytest
from dateutil.relativedelta import relativedelta
from pytest_mock.plugin import MockerFixture

from opal.caregivers import factories as caregiver_factories
from opal.hospital_settings import factories as hospital_factories
from opal.legacy import factories, models
from opal.legacy import utils as legacy_utils
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipType
from opal.services.reports.questionnaire import Question, QuestionnaireData

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_user_sernum() -> None:
    """Test get_patient_sernum method."""
    factories.LegacyUserFactory()
    user = models.LegacyUsers.objects.all()[0]
    sernum = legacy_utils.get_patient_sernum(user.username)

    assert sernum == user.usertypesernum


def test_get_user_sernum_no_user_available() -> None:
    """Test get_patient_sernum method when no user are found."""
    sernum = legacy_utils.get_patient_sernum('random_string')

    assert sernum == 0


def test_create_patient() -> None:
    """The patient is created successfully."""
    legacy_patient = legacy_utils.create_patient(
        'Marge',
        'Simpson',
        models.LegacySexType.FEMALE,
        datetime.date(1986, 10, 5),
        'marge@opalmedapps.ca',
        models.LegacyLanguage.FRENCH,
        'SIMM86600599',
        models.LegacyAccessLevel.NEED_TO_KNOW,
    )

    legacy_patient.full_clean()

    assert legacy_patient.first_name == 'Marge'
    assert legacy_patient.last_name == 'Simpson'
    assert legacy_patient.sex == models.LegacySexType.FEMALE
    assert legacy_patient.date_of_birth == timezone.make_aware(datetime.datetime(1986, 10, 5))
    assert legacy_patient.email == 'marge@opalmedapps.ca'
    assert legacy_patient.language == models.LegacyLanguage.FRENCH
    assert legacy_patient.ramq == 'SIMM86600599'
    assert legacy_patient.access_level == models.LegacyAccessLevel.NEED_TO_KNOW


def test_create_dummy_patient() -> None:
    """The dummy patient is created successfully."""
    legacy_patient = legacy_utils.create_dummy_patient(
        'Marge',
        'Simpson',
        'marge@opalmedapps.ca',
        models.LegacyLanguage.FRENCH,
    )

    legacy_patient.full_clean()

    date_of_birth = timezone.make_aware(datetime.datetime(1900, 1, 1))

    assert legacy_patient.first_name == 'Marge'
    assert legacy_patient.last_name == 'Simpson'
    assert legacy_patient.sex == models.LegacySexType.UNKNOWN
    assert legacy_patient.date_of_birth == date_of_birth
    assert legacy_patient.email == 'marge@opalmedapps.ca'
    assert legacy_patient.language == models.LegacyLanguage.FRENCH
    assert legacy_patient.ramq == ''
    assert legacy_patient.access_level == models.LegacyAccessLevel.ALL


def test_update_patient() -> None:
    """An existing dummy patient is updated successfully."""
    # the date of birth for dummy patients is 0000-00-00 but it fails validation since it is an invalid date
    legacy_patient = factories.LegacyPatientFactory(
        ramq='',
        date_of_birth=timezone.make_aware(datetime.datetime(2000, 1, 1)),
        sex=models.LegacySexType.UNKNOWN,
        age=None,
    )

    date_of_birth = timezone.make_aware(datetime.datetime(2008, 3, 29))
    legacy_utils.update_patient(legacy_patient, models.LegacySexType.OTHER, date_of_birth.date(), 'SIMB08032999')

    legacy_patient.refresh_from_db()

    expected_age = relativedelta(timezone.now(), date_of_birth)

    assert legacy_patient.sex == models.LegacySexType.OTHER
    assert legacy_patient.date_of_birth == date_of_birth
    assert legacy_patient.age == expected_age.years
    assert legacy_patient.ramq == 'SIMB08032999'


def test_insert_hospital_identifiers() -> None:
    """The patient's hospital identifiers are added for the legacy patient."""
    rvh = hospital_factories.Site(acronym='RVH')
    mgh = hospital_factories.Site(acronym='MGH')
    mch = hospital_factories.Site(acronym='MCH')

    patient = patient_factories.Patient()
    patient_factories.HospitalPatient(patient=patient, mrn='9999995', site=rvh)
    patient2 = patient_factories.Patient(ramq='SIMB08032999')
    patient_factories.HospitalPatient(patient=patient2, mrn='1234567', site=rvh)

    legacy_patient = factories.LegacyPatientFactory(patientsernum=patient.legacy_id)

    factories.LegacyHospitalIdentifierTypeFactory(code='RVH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MGH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MCH')

    legacy_utils.insert_hospital_identifiers(legacy_patient, [
        (rvh, '9999995', True),
        (mgh, '7654321', True),
        (mch, '1234567', False),
    ])

    assert models.LegacyPatientHospitalIdentifier.objects.count() == 3
    assert models.LegacyPatientHospitalIdentifier.objects.filter(patient=legacy_patient).count() == 3
    assert models.LegacyPatientHospitalIdentifier.objects.filter(
        mrn='9999995', hospital__code='RVH', is_active=True,
    ).exists()
    assert models.LegacyPatientHospitalIdentifier.objects.filter(
        mrn='7654321', hospital__code='MGH', is_active=True,
    ).exists()
    assert models.LegacyPatientHospitalIdentifier.objects.filter(
        mrn='1234567', hospital__code='MCH', is_active=False,
    ).exists()


def test_create_patient_control() -> None:
    """The patient control is created for the legacy patient."""
    legacy_patient = factories.LegacyPatientFactory(patientsernum=321)

    legacy_utils.create_patient_control(legacy_patient)

    assert models.LegacyPatientControl.objects.count() == 1
    assert models.LegacyPatientControl.objects.get().patient_id == 321


def test_initialize_new_patient() -> None:
    """A legacy patient is initialized from an existing patient."""
    patient = patient_factories.Patient(ramq='SIMB04100199')

    factories.LegacyHospitalIdentifierTypeFactory(code='RVH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MGH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MCH')

    legacy_patient = legacy_utils.initialize_new_patient(
        patient,
        [
            (hospital_factories.Site(acronym='RVH'), '9999995', True),
            (hospital_factories.Site(acronym='MGH'), '7654321', True),
            (hospital_factories.Site(acronym='MCH'), '1234567', False),
        ],
        self_caregiver=None,
    )

    assert models.LegacyPatient.objects.get() == legacy_patient
    assert legacy_patient.first_name == patient.first_name
    assert legacy_patient.last_name == patient.last_name
    assert legacy_patient.sex == models.LegacySexType.MALE
    assert legacy_patient.date_of_birth == timezone.make_aware(datetime.datetime(1999, 1, 1))
    assert legacy_patient.email == ''
    assert legacy_patient.language == models.LegacyLanguage.FRENCH
    assert legacy_patient.ramq == patient.ramq
    assert legacy_patient.access_level == models.LegacyAccessLevel.ALL
    assert models.LegacyPatientHospitalIdentifier.objects.filter(patient=legacy_patient).count() == 3
    assert models.LegacyPatientControl.objects.get().patient_id == legacy_patient.patientsernum


def test_initialize_new_patient_no_ramq() -> None:
    """A legacy patient is initialized from an existing patient that has no RAMQ."""
    patient = patient_factories.Patient(ramq='')

    legacy_patient = legacy_utils.initialize_new_patient(patient, [], None)

    assert legacy_patient.ramq == ''


def test_initialize_new_patient_existing_caregiver() -> None:
    """A legacy patient is initialized from an existing patient that is their own caregiver."""
    patient = patient_factories.Patient()
    caregiver = caregiver_factories.CaregiverProfile()

    legacy_patient = legacy_utils.initialize_new_patient(patient, [], caregiver)

    assert legacy_patient.email == caregiver.user.email
    assert legacy_patient.language == models.LegacyLanguage.ENGLISH


def test_create_user() -> None:
    """The legacy user is created successfully."""
    legacy_user = legacy_utils.create_user(models.LegacyUserType.CAREGIVER, 123, 'test-username')

    legacy_user.full_clean()

    assert legacy_user.usertype == models.LegacyUserType.CAREGIVER
    assert legacy_user.usertypesernum == 123
    assert legacy_user.username == 'test-username'


def test_update_legacy_user_type() -> None:
    """Ensure that a legacy user's type can be updated."""
    legacy_user = factories.LegacyUserFactory(usertype=models.LegacyUserType.CAREGIVER)
    legacy_utils.update_legacy_user_type(legacy_user.usersernum, models.LegacyUserType.PATIENT)
    legacy_user.refresh_from_db()

    assert legacy_user.usertype == models.LegacyUserType.PATIENT


def test_create_caregiver_user_patient() -> None:
    """The caregiver user is created for a patient."""
    legacy_patient = legacy_utils.create_patient(
        'Marge',
        'Simpson',
        models.LegacySexType.FEMALE,
        datetime.date(1986, 10, 5),
        '',
        models.LegacyLanguage.ENGLISH,
        'SIMM86600599',
        models.LegacyAccessLevel.NEED_TO_KNOW,
    )
    relationship = patient_factories.Relationship(
        patient__legacy_id=legacy_patient.patientsernum,
        type=RelationshipType.objects.self_type(),
    )

    legacy_user = legacy_utils.create_caregiver_user(relationship, 'test-username', 'fr', 'marge@opalmedapps.ca')

    # no additional dummy patient was created
    assert models.LegacyPatient.objects.count() == 1
    assert legacy_user.usertype == models.LegacyUserType.PATIENT
    assert legacy_user.usertypesernum == legacy_patient.patientsernum
    assert legacy_user.username == 'test-username'

    legacy_patient.refresh_from_db()
    assert legacy_patient.email == 'marge@opalmedapps.ca'
    assert legacy_patient.language == models.LegacyLanguage.FRENCH


def test_create_caregiver_user_caregiver() -> None:
    """The caregiver user is created for a non-patient."""
    relationship = patient_factories.Relationship(
        patient__legacy_id=None,
        caregiver__user__first_name='John',
        caregiver__user__last_name='Wayne',
    )

    legacy_user = legacy_utils.create_caregiver_user(relationship, 'test-username', 'fr', 'marge@opalmedapps.ca')

    # a dummy patient was created
    assert models.LegacyPatient.objects.count() == 1
    legacy_patient = models.LegacyPatient.objects.get()
    assert legacy_patient.first_name == 'John'
    assert legacy_patient.last_name == 'Wayne'
    assert legacy_patient.language == models.LegacyLanguage.FRENCH
    assert legacy_patient.email == 'marge@opalmedapps.ca'

    assert legacy_user.usertype == models.LegacyUserType.CAREGIVER
    assert legacy_user.usertypesernum == legacy_patient.patientsernum
    assert legacy_user.username == 'test-username'


def test_change_caregiver_user_to_patient() -> None:
    """The caregiver user is updated to a patient user."""
    patient = patient_factories.Patient(ramq='SIMB04100199')
    legacy_patient = legacy_utils.create_dummy_patient(
        'Marge',
        'Simpson',
        'marge@opalmedapps.ca',
        models.LegacyLanguage.ENGLISH,
    )
    legacy_user = factories.LegacyUserFactory(
        usertype=models.LegacyUserType.CAREGIVER,
        usertypesernum=legacy_patient.patientsernum,
    )

    legacy_utils.change_caregiver_user_to_patient(legacy_user.usersernum, patient)

    legacy_user.refresh_from_db()
    assert legacy_user.usertype == models.LegacyUserType.PATIENT

    legacy_patient.refresh_from_db()
    assert legacy_patient.sex == models.LegacySexType.MALE
    assert legacy_patient.ramq == 'SIMB04100199'
    assert legacy_patient.date_of_birth == timezone.make_aware(datetime.datetime(1999, 1, 1))

#  Unit test for questionnaires data processing


@pytest.mark.django_db
def test_get_questionnaire_data_success(mocker: MockerFixture) -> None:
    """Test successful execution of get_questionnaire_data."""
    # Arrange
    patient = patient_factories.Patient.create(legacy_id=123)
    mock_query_result = [('{"questionnaire_id": 1, "questions": []}',)]
    mock_parsed_data = [{'questionnaire_id': 1, 'questions': []}]
    mock_processed_data = [
        QuestionnaireData(
            questionnaire_id=1,
            questionnaire_title='Mock Title',
            last_updated=datetime.datetime(2023, 1, 1, 12, 0),
            questions=[],
        ),
    ]

    mock_fetch = mocker.patch(
        'opal.legacy.utils.fetch_questionnaires_from_db', return_value=mock_query_result,
    )
    mock_parse = mocker.patch(
        'opal.legacy.utils.parse_query_result', return_value=mock_parsed_data,
    )
    mock_process = mocker.patch(
        'opal.legacy.utils.process_questionnaire_data', return_value=mock_processed_data,
    )

    # Act
    result = legacy_utils.get_questionnaire_data(patient)

    # Assert
    mock_fetch.assert_called_once_with(123)
    mock_parse.assert_called_once_with(mock_query_result)
    mock_process.assert_called_once_with(mock_parsed_data)
    assert result == mock_processed_data


@pytest.mark.django_db
def test_get_questionnaire_data_db_error(mocker: MockerFixture) -> None:
    """Test database error handling in get_questionnaire_data."""
    patient = patient_factories.Patient.create(legacy_id=123)

    mock_fetch = mocker.patch(
        'opal.legacy.utils.fetch_questionnaires_from_db', side_effect=Exception('DB Error'),
    )

    with pytest.raises(CommandError, match='Error fetching questionnaires: DB Error'):
        legacy_utils.get_questionnaire_data(patient)

    mock_fetch.assert_called_once_with(123)


@pytest.mark.django_db
def test_get_questionnaire_data_parsing_error(mocker: MockerFixture) -> None:
    """Test JSON parsing error handling in get_questionnaire_data."""
    patient = patient_factories.Patient.create(legacy_id=123)
    mock_query_result = [('',)]

    mock_fetch = mocker.patch(
        'opal.legacy.utils.fetch_questionnaires_from_db', return_value=mock_query_result,
    )

    with pytest.raises(CommandError, match='Error parsing questionnaires: Expected parsed data to be a dict'):
        legacy_utils.get_questionnaire_data(patient)

    mock_fetch.assert_called_once_with(123)


@pytest.mark.django_db(databases=['questionnaire'])
def test_fetch_questionnaire_from_db(mocker: MockerFixture) -> None:
    """Test successful execution of fetch_questionnaires_from_db in the test questionnaire database."""
    external_patient_id = 51
    result = legacy_utils.fetch_questionnaires_from_db(external_patient_id)

    assert len(result) == 1
    assert result[0]['questionnaire_id'] == 12
    assert result[0]['questionnaire_nickname'] == 'Edmonton Symptom Assessment System'


def test_parse_query_result_success() -> None:
    """Test successful parsing of query results."""
    query_result = [
        {'questionnaire': 'questionnaire_value'},
        [{'questionnaire1': 'questionnaire_value1'}, {'questionnaire2': 'questionnaire_value2'}],
        [
            {'questionnaire3': 'questionnaire_value3'},
            {'questionnaire4': 'questionnaire_value4'},
            {'questionnaire5': 'questionnaire_value5'},
        ],
    ]
    expected_output = [
        {'questionnaire': 'questionnaire_value'},
        {'questionnaire1': 'questionnaire_value1'},
        {'questionnaire2': 'questionnaire_value2'},
        {'questionnaire3': 'questionnaire_value3'},
        {'questionnaire4': 'questionnaire_value4'},
        {'questionnaire5': 'questionnaire_value5'},
    ]

    result = legacy_utils.parse_query_result(query_result)

    assert result == expected_output


def test_parse_query_result_invalid_data() -> None:
    """Test parsing with invalid data in the query result."""
    query_result = [123, 'not_a_dict_or_list']  # Invalid data after deserialization
    with pytest.raises(ValueError, match='Expected parsed data to be a dict or list of dicts, got'):
        legacy_utils.parse_query_result(query_result)


def test_parse_query_result_empty_rows() -> None:
    """Test parsing when rows contain empty data."""
    query_result = list('')
    result = legacy_utils.parse_query_result(query_result)
    assert not result


def test_parse_query_result_non_dict_list() -> None:
    """Test parsing when data doesn't resolve to a list of dictionaries."""
    query_result = [['not_a_dict_list']]  # A list of invalid structures
    with pytest.raises(ValueError, match='Expected parsed data to be a dict or list of dicts, got'):
        legacy_utils.parse_query_result(query_result)


def test_parse_query_result_non_dict_items() -> None:
    """Test parsing when data contains non-dictionary items."""
    query_result = [[123, 456], None]  # A mix of invalid list contents
    with pytest.raises(ValueError, match='Expected parsed data to be a dict or list of dicts, got'):
        legacy_utils.parse_query_result(query_result)


def test_process_questionnaire_data(mocker: MockerFixture) -> None:
    """Test processing parsed questionnaire data into QuestionnaireData Objects."""
    mock_question = mocker.Mock(spec=Question)
    parsed_data_list = [
        {
            'questionnaire_id': 1,
            'questionnaire_nickname': 'Test Questionnaire',
            'last_updated': '2024-11-25 10:00:00',
            'questions': [{'question_text': 'Sample question', 'values': []}],
        },
    ]

    mock_process_questions = mocker.patch(
        'opal.legacy.utils.process_questions', return_value=[mock_question],
    )

    result = legacy_utils.process_questionnaire_data(parsed_data_list)
    assert len(result) == 1
    assert result[0].questionnaire_id == 1
    assert result[0].questionnaire_title == 'Test Questionnaire'
    assert result[0].last_updated == datetime.datetime(
        2024,
        11,
        25,
        10,
        0,
        0,
    )
    assert result[0].questions == [mock_question]

    mock_process_questions.assert_called_once_with(
        [{'question_text': 'Sample question', 'values': []}],
    )


def test_process_questionnaire_data_missing_questions(mocker: MockerFixture) -> None:
    """Test processing with missing `questions` key."""
    parsed_data_list = [
        {
            'questionnaire_id': 1,
            'questionnaire_nickname': 'Test Questionnaire',
            'last_updated': 'invalid_date',
        },
    ]

    with pytest.raises(CommandError, match='Unexpected data format:'):
        legacy_utils.process_questionnaire_data(parsed_data_list)


def test_process_questionnaire_data_invalid_date_format(mocker: MockerFixture) -> None:
    """Test processing with invalid `last_updated` date format."""
    parsed_data_list = [
        {
            'questionnaire_id': 1,
            'questionnaire_nickname': 'Test Questionnaire',
            'last_updated': 'invalid-date',
            'questions': [{
                'question_text': 'Sample question',
                'question_label': 'Sample label',
                'question_type_id': 1,
                'position': 1,
                'min_value': None,
                'max_value': None,
                'polarity': None,
                'section_id': 1,
                'values': [],
            },
            ],
        },
    ]

    with pytest.raises(ValueError, match="time data 'invalid-date' does not match format "):
        legacy_utils.process_questionnaire_data(parsed_data_list)


def test_process_questions_valid() -> None:
    """Test processing parsed questions data into Question Objects."""
    parsed_question_list = [
        {
            'question_text': 'Sample question',
            'question_label': 'Question label',
            'question_type_id': 1,
            'position': 1,
            'min_value': None,
            'max_value': None,
            'polarity': 1,
            'section_id': 1,
            'values': [
                [
                    '2024-02-23 12:00:00', '3',
                ],
            ],
        },
    ]
    result = legacy_utils.process_questions(parsed_question_list)

    assert len(result) == 1
    assert result[0].question_text == 'Sample question'
    assert result[0].question_label == 'Question label'
    assert result[0].question_type_id == 1
    assert result[0].position == 1
    assert result[0].polarity == 1
    assert result[0].section_id == 1
    assert result[0].values == [
        (datetime.datetime(2024, 2, 23, 12, 0), '3'),
    ]


def test_invalid_question_format() -> None:
    """Test processing with invalid question format."""
    parsed_question_list = ['not a dict']

    with pytest.raises(CommandError, match='Invalid question format: not a dict'):
        legacy_utils.process_questions(parsed_question_list)


def test_invalid_question_values_format() -> None:
    """Test processing with invalid question values format."""
    parsed_question_list = [
        {
            'question_text': 'Sample question',
            'question_label': 'Question label',
            'question_type_id': 1,
            'position': 1,
            'min_value': None,
            'max_value': None,
            'polarity': 1,
            'section_id': 1,
            'values': 'invalid format',
        },
    ]

    with pytest.raises(CommandError, match="Invalid 'values' format for question"):
        legacy_utils.process_questions(parsed_question_list)


def test_invalid_question_date_format() -> None:
    """Test processing with invalid question values format."""
    parsed_question_list = [
        {
            'question_text': 'Sample question',
            'question_label': 'Question label',
            'question_type_id': 1,
            'position': 1,
            'min_value': None,
            'max_value': None,
            'polarity': 1,
            'section_id': 1,
            'values': [
                [
                    '2024-23-02 12:00:00', '3',  # Should be '2024-02-23-...'
                ],
            ],
        },
    ]

    with pytest.raises(ValueError, match="time data '2024-23-02 12:00:00' does not match format "):
        legacy_utils.process_questions(parsed_question_list)


@pytest.fixture
def patient_mock(mocker: MockerFixture) -> Any:
    """Fixture to create a mock patient."""
    return mocker.MagicMock(
        first_name='Bart',
        last_name='Simpson',
        date_of_birth=datetime.date(1999, 1, 1),
        ramq='SIMM99999999',
        sites_and_mrns=[
            {'mrn': '22222443', 'site_code': 'MGH'},
            {'mrn': '1111728', 'site_code': 'RVH'},
        ],
    )


@pytest.fixture
def mock_institution(mocker: MockerFixture) -> Any:
    """Fixture to mock Institution.objects.get."""
    institution_mock = mocker.MagicMock()
    institution_mock.logo.path = Path('opal/tests/fixtures/test_logo.png')  # Set mock path
    mocker.patch('opal.hospital_settings.models.Institution.objects.get', return_value=institution_mock)
    return institution_mock


@pytest.fixture
def questionnaire_data_mock(mocker: MockerFixture) -> Any:
    """Fixture to create a mock questionnaire data list."""
    question_mock = mocker.MagicMock(
        question_text='Sample question',
        question_label='Sample label',
        question_type_id=1,
        position=1,
        min_value=0,
        max_value=10,
        polarity=1,
        section_id=1,
        values=[
            (
                datetime.datetime(2024, 11, 25, 10, 0, 0), '3',
            ),
        ],
    )
    return [
        mocker.MagicMock(
            questionnaire_id=1,
            questionnaire_title='Test Questionnaire',
            last_updated=datetime.datetime(2024, 11, 25, 10, 0, 0),
            questions=[question_mock],
        ),
    ]


@pytest.fixture
def mock_generate_pdf(mocker: MockerFixture) -> Any:
    """Fixture to mock generate_pdf."""
    return mocker.patch('opal.legacy.utils.generate_pdf', autospec=True)

# Test for generating the report


def test_generate_questionnaire_report(
    mocker: MockerFixture,
    patient_mock: Any, mock_institution: Any, questionnaire_data_mock: Any, mock_generate_pdf: Any,  # noqa: WPS442
) -> None:
    """Test for generating the questionnaire report with the appropriate data."""
    mock_generate_pdf.return_value = bytearray(b'fake-pdf-bytearray')
    result = legacy_utils.generate_questionnaire_report(
        patient_mock,
        questionnaire_data_mock,
    )

    mock_generate_pdf.assert_called_once()
    args = mock_generate_pdf.call_args.kwargs

    # Verify patient data
    assert args['patient'].patient_first_name == 'Bart'
    assert args['patient'].patient_last_name == 'Simpson'
    assert args['patient'].patient_date_of_birth == datetime.date(1999, 1, 1)
    assert args['patient'].patient_ramq == 'SIMM99999999'

    # Verify questionnaire data
    assert len(args['questionnaires']) == 1
    questionnaire = args['questionnaires'][0]
    assert questionnaire.questionnaire_id == 1
    assert questionnaire.questionnaire_title == 'Test Questionnaire'
    assert questionnaire.last_updated == datetime.datetime(2024, 11, 25, 10, 0, 0)

    # Verify questions
    question = questionnaire.questions[0]
    assert question.question_text == 'Sample question'
    assert question.question_label == 'Sample label'
    assert question.question_type_id == 1
    assert question.min_value == 0
    assert question.max_value == 10
    assert question.values == [(
        datetime.datetime(2024, 11, 25, 10, 0, 0), '3',
    )]

    # Verify pdf generation
    assert isinstance(result, bytearray), 'Output'
    assert result, 'PDF should not be empty'


def test_path_to_questionnaire_report(mocker: MockerFixture, patient_mock: Any) -> None:  # noqa: WPS442
    """Test `path_to_questionnaire_report`."""
    mock_localtime = mocker.patch(
        'opal.legacy.utils.timezone.localtime',
        return_value=datetime.datetime(2023, 1, 1, 12, 0, 0),
    )
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    pdf_report = bytearray(b'PDF content')
    expected_filename = 'Bart_Simpson_2023-Jan-01_12-00-00_questionnaire.pdf'
    expected_path = settings.QUESTIONNAIRE_REPORTS_PATH / f'{expected_filename}.pdf'

    result = legacy_utils.path_to_questionnaire_report(patient_mock, pdf_report)

    # Assertions
    assert result == expected_path
    mock_open.assert_called_once_with(expected_path, 'wb')
    mock_open().write.assert_called_once_with(pdf_report)
    mock_localtime.assert_called_once()
