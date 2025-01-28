import datetime as dt
from pathlib import Path
from typing import Any

from django.db import OperationalError
from django.utils import timezone

import pytest
from dateutil.relativedelta import relativedelta
from pytest_mock.plugin import MockerFixture

from opal.caregivers import factories as caregiver_factories
from opal.hospital_settings import factories as hospital_factories
from opal.hospital_settings.models import Institution
from opal.legacy import factories, models
from opal.legacy import utils as legacy_utils
from opal.legacy_questionnaires import factories as questionnaire_factories
from opal.legacy_questionnaires import models as questionnaire_models
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipType
from opal.services.reports.questionnaire import Question, QuestionnaireData, QuestionType

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


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
        dt.date(1986, 10, 5),
        'marge@opalmedapps.ca',
        models.LegacyLanguage.FRENCH,
        'SIMM86600599',
        models.LegacyAccessLevel.NEED_TO_KNOW,
    )

    legacy_patient.full_clean()

    assert legacy_patient.first_name == 'Marge'
    assert legacy_patient.last_name == 'Simpson'
    assert legacy_patient.sex == models.LegacySexType.FEMALE
    assert legacy_patient.date_of_birth == timezone.make_aware(dt.datetime(1986, 10, 5))
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

    date_of_birth = timezone.make_aware(dt.datetime(1900, 1, 1))

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
        date_of_birth=timezone.make_aware(dt.datetime(2000, 1, 1)),
        sex=models.LegacySexType.UNKNOWN,
        age=None,
    )

    date_of_birth = timezone.make_aware(dt.datetime(2008, 3, 29))
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
    assert legacy_patient.date_of_birth == timezone.make_aware(dt.datetime(1999, 1, 1))
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
        dt.date(1986, 10, 5),
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
    assert legacy_patient.date_of_birth == timezone.make_aware(dt.datetime(1999, 1, 1))


def test_databank_consent_form_fixture(
    databank_consent_questionnaire_data: tuple[questionnaire_models.LegacyQuestionnaire, models.LegacyEducationalMaterialControl],  # noqa: E501
) -> None:
    """Test the fixture from conftest creates a proper consent questionnaire."""
    info_sheet = databank_consent_questionnaire_data[1]
    consent_questionnaire = databank_consent_questionnaire_data[0]

    assert info_sheet.educational_material_type_en == 'Factsheet'
    assert info_sheet.name_en == 'Information and Consent Factsheet - QSCC Databank'

    assert consent_questionnaire.title.content == 'QSCC Databank Information'
    assert consent_questionnaire.purpose.title.content == 'Consent'


def test_fetch_databank_control_records(
    databank_consent_questionnaire_data: tuple[questionnaire_models.LegacyQuestionnaire, models.LegacyEducationalMaterialControl],  # noqa: E501
) -> None:
    """Test the fetching of key foreign key data used for consent form creation."""
    # Setup patient records
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    factories.LegacyPatientFactory(patientsernum=django_patient.legacy_id)
    legacy_qdb_patient = questionnaire_factories.LegacyQuestionnairePatientFactory(external_id=django_patient.legacy_id)
    consent_form = databank_consent_questionnaire_data[0]
    info_sheet = databank_consent_questionnaire_data[1]
    result = legacy_utils.fetch_databank_control_records(django_patient)
    if result:
        fetched_info_sheet, fetched_qdb_patient, fetched_qdb_questionnaire_control, fetched_questionnaire_control = result  # noqa: E501

    assert all([
        result,
        fetched_info_sheet,
        fetched_qdb_patient,
        fetched_qdb_questionnaire_control,
        fetched_questionnaire_control,
    ])

    assert legacy_qdb_patient.external_id == int(fetched_qdb_patient.external_id)
    # In this case we created the QDB Patient before calling the function, so it should be Test user from the factory
    assert fetched_qdb_patient.created_by == 'Test User'
    assert info_sheet.name_en == fetched_info_sheet.name_en
    assert consent_form.title.content == fetched_qdb_questionnaire_control.title.content
    assert fetched_questionnaire_control.questionnaire_name_en == 'QSCC Databank Information'
    assert fetched_questionnaire_control.questionnaire_db_ser_num == fetched_qdb_questionnaire_control.id


def test_fetch_databank_control_records_patient_creation(
    databank_consent_questionnaire_data: tuple[questionnaire_models.LegacyQuestionnaire, models.LegacyEducationalMaterialControl],  # noqa: E501
) -> None:
    """Test that the function will create a QDB_Patient record if one hasnt been created already."""
    # Setup patient records
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    factories.LegacyPatientFactory(patientsernum=django_patient.legacy_id)
    consent_form = databank_consent_questionnaire_data[0]
    info_sheet = databank_consent_questionnaire_data[1]
    result = legacy_utils.fetch_databank_control_records(django_patient)
    if result:
        fetched_info_sheet, fetched_qdb_patient, fetched_qdb_questionnaire_control, fetched_questionnaire_control = result  # noqa: E501

    assert all([
        result,
        fetched_info_sheet,
        fetched_qdb_patient,
        fetched_qdb_questionnaire_control,
        fetched_questionnaire_control,
    ])

    assert fetched_qdb_patient.external_id == django_patient.legacy_id
    assert fetched_qdb_patient.created_by == 'DJANGO_AUTO_CREATE_DATABANK_CONSENT'

    assert info_sheet.name_en == fetched_info_sheet.name_en
    assert consent_form.title.content == fetched_qdb_questionnaire_control.title.content
    assert fetched_questionnaire_control.questionnaire_name_en == 'QSCC Databank Information'
    assert fetched_questionnaire_control.questionnaire_db_ser_num == fetched_qdb_questionnaire_control.id


def test_fetch_databank_control_records_not_found() -> None:
    """Test behaviour when one of the required controls isn't found."""
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    factories.LegacyPatientFactory(patientsernum=django_patient.legacy_id)
    result = legacy_utils.fetch_databank_control_records(django_patient)

    assert not result


def test_create_databank_patient_consent_data_records_not_found() -> None:
    """Test behaviour when control records are not found."""
    # Setup patient records
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    factories.LegacyPatientFactory(patientsernum=django_patient.legacy_id)

    assert not legacy_utils.create_databank_patient_consent_data(django_patient)


def test_create_databank_patient_consent_data(
    databank_consent_questionnaire_data: tuple[questionnaire_models.LegacyQuestionnaire, models.LegacyEducationalMaterialControl],  # noqa: E501
) -> None:
    """Test creation of databank consent form and information sheet for patient."""
    # Setup patient records
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    legacy_patient = factories.LegacyPatientFactory(patientsernum=django_patient.legacy_id)

    consent_form = databank_consent_questionnaire_data[0]
    info_sheet = databank_consent_questionnaire_data[1]
    response = legacy_utils.create_databank_patient_consent_data(django_patient)

    qdb_patient = questionnaire_models.LegacyQuestionnairePatient.objects.get(
        external_id=django_patient.legacy_id,
    )
    inserted_answer_questionnaire = questionnaire_models.LegacyAnswerQuestionnaire.objects.get(
        questionnaire_id=consent_form.id,
        patient_id=qdb_patient.id,
    )
    inserted_sheet = models.LegacyEducationalMaterial.objects.get(
        educationalmaterialcontrolsernum=info_sheet,
        patientsernum=django_patient.legacy_id,
    )
    inserted_questionnaire = models.LegacyQuestionnaire.objects.get(
        patientsernum=django_patient.legacy_id,
        patient_questionnaire_db_ser_num=inserted_answer_questionnaire.id,
    )

    assert response
    assert all([qdb_patient, inserted_answer_questionnaire, inserted_sheet, inserted_questionnaire])

    assert qdb_patient.created_by == 'DJANGO_AUTO_CREATE_DATABANK_CONSENT'

    assert inserted_questionnaire.completedflag == 0
    assert inserted_questionnaire.patientsernum == legacy_patient
    assert inserted_questionnaire.patient_questionnaire_db_ser_num == inserted_answer_questionnaire.id

    assert inserted_sheet.readstatus == 0
    assert inserted_sheet.patientsernum == legacy_patient
    assert inserted_sheet.educationalmaterialcontrolsernum == info_sheet

    assert inserted_answer_questionnaire.status == 0
    assert inserted_answer_questionnaire.patient_id == qdb_patient.id
    assert inserted_answer_questionnaire.questionnaire_id == consent_form.id


def test_legacy_patient_not_found(
    databank_consent_questionnaire_data: tuple[questionnaire_models.LegacyQuestionnaire, models.LegacyEducationalMaterialControl],  # noqa: E501
) -> None:
    """Test behaviour when the legacy patient record is not found."""
    # Setup patient records
    django_patient = patient_factories.Patient(ramq='SIMB04100199')
    assert not legacy_utils.create_databank_patient_consent_data(django_patient)


#  Unit test for questionnaires data processing
@pytest.mark.django_db(databases=['questionnaire', 'default'])
def test_get_questionnaire_data_success(mocker: MockerFixture, questionnaire_data: None) -> None:
    """Test that get_questionnaire_data returns the expected data."""
    patient = patient_factories.Patient.create(legacy_id=51)
    questionnaire_result = legacy_utils.get_questionnaire_data(patient)

    assert len(questionnaire_result) == 1
    assert questionnaire_result[0].questionnaire_title == 'Edmonton Symptom Assessment System'


@pytest.mark.django_db(databases=['questionnaire', 'default'])
def test_get_questionnaire_data_no_patient(mocker: MockerFixture) -> None:
    """Test that get_questionnaire_data with wrong patient id."""
    patient = patient_factories.Patient.create(legacy_id=0)

    with pytest.raises(legacy_utils.DataFetchError, match='The patient has no legacy id.'):
        legacy_utils.get_questionnaire_data(patient)


@pytest.mark.django_db
def test_get_questionnaire_data_db_error(mocker: MockerFixture) -> None:
    """Test database error handling in get_questionnaire_data."""
    patient = patient_factories.Patient.create(legacy_id=123)

    mock_fetch = mocker.patch(
        'opal.legacy.utils._fetch_questionnaires_from_db', side_effect=OperationalError('DB Error'),
    )

    with pytest.raises(legacy_utils.DataFetchError, match='DB Error'):
        legacy_utils.get_questionnaire_data(patient)

    mock_fetch.assert_called_once_with(123)


@pytest.mark.django_db
def test_get_questionnaire_data_parsing_error(mocker: MockerFixture) -> None:
    """Test JSON parsing error handling in get_questionnaire_data."""
    patient = patient_factories.Patient.create(legacy_id=123)
    mock_query_result = [('',)]

    mock_fetch = mocker.patch(
        'opal.legacy.utils._fetch_questionnaires_from_db', return_value=mock_query_result,
    )

    with pytest.raises(legacy_utils.DataFetchError, match='Expected parsed data'):
        legacy_utils.get_questionnaire_data(patient)

    mock_fetch.assert_called_once_with(123)


@pytest.mark.django_db(databases=['questionnaire'])
def test_fetch_questionnaire_from_db(mocker: MockerFixture, questionnaire_data: None) -> None:
    """Test successful execution of fetch_questionnaires_from_db in the test questionnaire database."""
    external_patient_id = 51
    result = legacy_utils._fetch_questionnaires_from_db(external_patient_id)

    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]['questionnaire_id'] == 12
    assert result[0]['questionnaire_nickname'] == 'Edmonton Symptom Assessment System'


def test_parse_query_result_success() -> None:
    """Test successful parsing of query results."""
    query_result: list[dict[str, Any] | list[dict[str, Any]]] = [
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

    result = legacy_utils._parse_query_result(query_result)

    assert result == expected_output


def test_parse_query_result_empty_rows() -> None:
    """Test parsing when rows contain empty data."""
    query_result: list[dict[str, Any] | list[dict[str, Any]]] = []
    result = legacy_utils._parse_query_result(query_result)
    assert not result


def test_process_questionnaire_data(mocker: MockerFixture) -> None:
    """Test processing parsed questionnaire data into QuestionnaireData Objects."""
    parsed_data_list = [
        {
            'questionnaire_id': 1,
            'questionnaire_nickname': 'Test Questionnaire',
            'last_updated': '2024-11-25 10:00:00.000000',
            'questions': [
                {
                    'question_text': 'Sample question',
                    'question_label': 'Sample label',
                    'question_type_id': 1,
                    'position': 1,
                    'min_value': 0,
                    'max_value': 0,
                    'polarity': 0,
                    'section_id': 1,
                    'values': [
                        [
                            '2024-02-23 12:00:00.000000', '3',
                        ],
                    ],
                },
            ],
        },
    ]

    result = legacy_utils._process_questionnaire_data(parsed_data_list)
    assert len(result) == 1
    assert result[0].questionnaire_id == 1
    assert result[0].questionnaire_title == 'Test Questionnaire'
    assert result[0].last_updated == dt.datetime(
        2024, 11, 25, 10, 0, 0,
    )
    assert result[0].questions[0].question_text == 'Sample question'
    assert result[0].questions[0].answers == [
        (dt.datetime(2024, 2, 23, 12, 0), '3'),
    ]


def test_process_questionnaire_data_missing_questions(mocker: MockerFixture) -> None:
    """Test processing with missing `questions` key."""
    parsed_data_list = [
        {
            'questionnaire_id': 1,
            'questionnaire_nickname': 'Test Questionnaire',
            'last_updated': 'invalid_date',
        },
    ]

    with pytest.raises(legacy_utils.DataFetchError, match='Unexpected data format:'):
        legacy_utils._process_questionnaire_data(parsed_data_list)


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

    with pytest.raises(ValueError, match="Invalid isoformat string: 'invalid-date'"):
        legacy_utils._process_questionnaire_data(parsed_data_list)


def test_process_questions_valid() -> None:
    """Test processing parsed questions data into Question Objects."""
    parsed_question_list = [
        {
            'question_text': 'Sample question',
            'question_label': 'Question label',
            'question_type_id': QuestionType.CHECKBOX,
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
    result = legacy_utils._process_questions(parsed_question_list)

    assert len(result) == 1
    assert result[0].question_text == 'Sample question'
    assert result[0].question_label == 'Question label'
    assert result[0].question_type_id == QuestionType.CHECKBOX
    assert result[0].position == 1
    assert result[0].polarity == 1
    assert result[0].section_id == 1
    assert result[0].answers == [
        (dt.datetime(2024, 2, 23, 12, 0), '3'),
    ]


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

    with pytest.raises(ValueError, match="Invalid type for 'answers'"):
        legacy_utils._process_questions(parsed_question_list)


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

    with pytest.raises(ValueError, match='month must be in '):
        legacy_utils._process_questions(parsed_question_list)


def questionnaire_data_mock() -> list[QuestionnaireData]:
    """Fixture to create a mock questionnaire data list."""
    question = Question(
        question_text='Sample question',
        question_label='Sample label',
        question_type_id=QuestionType.NUMERIC,
        position=1,
        min_value=0,
        max_value=10,
        polarity=1,
        section_id=1,
        answers=[
            (
                dt.datetime(2024, 11, 25, 10, 0, 0), '3',
            ),
        ],
    )
    return [
        QuestionnaireData(
            questionnaire_id=1,
            questionnaire_title='Test Questionnaire',
            last_updated=dt.datetime(2024, 11, 25, 10, 0, 0),
            questions=[question],
        ),
    ]


# Test for generating the report
def test_generate_questionnaire_report(mocker: MockerFixture) -> None:
    """Test for generating the questionnaire report with the appropriate data."""
    patient = patient_factories.Patient()
    patient_factories.HospitalPatient(patient=patient)
    institution = Institution.objects.get()

    mock_generate_pdf = mocker.patch('opal.services.reports.questionnaire.generate_pdf', autospec=True)
    mock_generate_pdf.return_value = bytearray(b'fake-pdf-bytearray')
    result = legacy_utils.generate_questionnaire_report(
        patient,
        questionnaire_data_mock(),
    )

    mock_generate_pdf.assert_called_once()
    args = mock_generate_pdf.call_args.kwargs

    # Verify patient data
    assert args['patient'].patient_first_name == 'Marge'
    assert args['patient'].patient_last_name == 'Simpson'
    assert args['patient'].patient_date_of_birth == dt.date(1999, 1, 1)

    # Verify institution
    actual_logo = args['institution'].institution_logo_path
    expected_logo = Path(institution.logo.path)

    assert actual_logo == expected_logo

    # Verify questionnaire data
    assert len(args['questionnaires']) == 1
    questionnaire = args['questionnaires'][0]
    assert questionnaire.questionnaire_id == 1
    assert questionnaire.questionnaire_title == 'Test Questionnaire'
    assert questionnaire.last_updated == dt.datetime(2024, 11, 25, 10, 0, 0)

    # Verify questions
    question = questionnaire.questions[0]
    assert question.question_text == 'Sample question'
    assert question.question_label == 'Sample label'
    assert question.question_type_id == QuestionType.NUMERIC
    assert question.min_value == 0
    assert question.max_value == 10
    assert question.answers == [(
        dt.datetime(2024, 11, 25, 10, 0, 0), '3',
    )]

    # Verify pdf generation
    assert isinstance(result, bytearray), 'Output'
    assert result, 'PDF should not be empty'
