"""Utility functions used by legacy API views."""
import datetime as dt
import json
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypeAlias, Union

from django.core.management.base import CommandError
from django.db import OperationalError, connections, models, transaction
from django.utils import timezone

from opal.caregivers.models import CaregiverProfile
from opal.hospital_settings.models import Institution, Site
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire
from opal.legacy_questionnaires.models import LegacyQuestionnaire as QDB_LegacyQuestionnaire
from opal.legacy_questionnaires.models import LegacyQuestionnairePatient
from opal.patients.models import Patient, Relationship
from opal.services.reports.base import InstitutionData, PatientData
from opal.services.reports.questionnaire import Question, QuestionnaireData, generate_pdf

from .models import (  # noqa: WPS235
    LegacyAccessLevel,
    LegacyEducationalMaterial,
    LegacyEducationalMaterialControl,
    LegacyLanguage,
    LegacyPatient,
    LegacyPatientControl,
    LegacyPatientHospitalIdentifier,
    LegacyQuestionnaire,
    LegacyQuestionnaireControl,
    LegacySexType,
    LegacyUsers,
    LegacyUserType,
)

#: Mapping from sex type to the corresponding legacy sex type
SEX_TYPE_MAPPING = MappingProxyType({
    Patient.SexType.MALE.value: LegacySexType.MALE,
    Patient.SexType.FEMALE.value: LegacySexType.FEMALE,
    Patient.SexType.OTHER.value: LegacySexType.OTHER,
    Patient.SexType.UNKNOWN.value: LegacySexType.UNKNOWN,
})

#: Mapping from data access type to the corresponding legacy access level
ACCESS_LEVEL_MAPPING = MappingProxyType({
    Patient.DataAccessType.ALL.value: LegacyAccessLevel.ALL,
    Patient.DataAccessType.NEED_TO_KNOW.value: LegacyAccessLevel.NEED_TO_KNOW,
})

DatabankControlRecords: TypeAlias = Union[
    tuple[
        LegacyEducationalMaterialControl,
        LegacyQuestionnairePatient,
        QDB_LegacyQuestionnaire,
        LegacyQuestionnaireControl,
    ],
    None,
]


def get_patient_sernum(username: str) -> int:
    """
    Get the patient sernum associated with the username to query the legacy database.

    Args:
        username: Firebase username making the request

    Returns:
        User patient sernum associated with the request username user name.
    """
    user = LegacyUsers.objects.filter(
        username=username,
        usertype=LegacyUserType.PATIENT,
    ).first()
    if user:
        return user.usertypesernum
    return 0


def create_patient(  # noqa: WPS211 (too many arguments)
    first_name: str,
    last_name: str,
    sex: LegacySexType,
    date_of_birth: dt.date,
    email: str,
    language: LegacyLanguage,
    ramq: str,
    access_level: LegacyAccessLevel,
) -> LegacyPatient:
    """
    Create a patient with the given properties.

    Args:
        first_name: the first name of the patient
        last_name: the last name of the patient
        sex: the sex of the patient
        date_of_birth: the date of birth of the patient
        email: the email of the patient
        language: the language of the patient
        ramq: the RAMQ of the patient
        access_level: the access level of the patient

    Returns:
        the legacy patient instance
    """
    age = Patient.calculate_age(date_of_birth)
    # the legacy DB stores the date of birth as a datetime
    datetime_of_birth = timezone.make_aware(dt.datetime(date_of_birth.year, date_of_birth.month, date_of_birth.day))

    patient = LegacyPatient(
        first_name=first_name,
        last_name=last_name,
        sex=sex,
        date_of_birth=datetime_of_birth,
        age=age,
        email=email,
        language=language,
        ramq=ramq,
        access_level=access_level,
    )
    patient.full_clean()
    patient.save()

    return patient


def create_dummy_patient(
    first_name: str,
    last_name: str,
    email: str,
    language: LegacyLanguage,
) -> LegacyPatient:
    """
    Create a dummy patient for a caregiver with the given properties.

    Uses sensible defaults for any date that is unknown.

    Args:
        first_name: the first name of the patient
        last_name: the last name of the patient
        email: the email of the patient
        language: the language of the patient

    Returns:
        the legacy patient instance
    """
    return create_patient(
        first_name=first_name,
        last_name=last_name,
        sex=LegacySexType.UNKNOWN,
        # requires a valid date; use a temporary date
        date_of_birth=timezone.make_aware(dt.datetime(1900, 1, 1)),  # noqa: WPS432
        email=email,
        language=language,
        ramq='',
        access_level=LegacyAccessLevel.ALL,
    )


def update_patient(patient: LegacyPatient, sex: LegacySexType, date_of_birth: dt.date, ramq: str) -> None:
    """
    Update an existing patient with the given properties.

    Args:
        patient: the patient to update
        sex: the sex of the patient
        date_of_birth: the date of birth of the patient
        ramq: the RAMQ of the patient
    """
    age = Patient.calculate_age(date_of_birth)
    # the legacy DB stores the date of birth as a datetime
    datetime_of_birth = timezone.make_aware(dt.datetime(date_of_birth.year, date_of_birth.month, date_of_birth.day))

    patient.sex = sex
    patient.date_of_birth = datetime_of_birth
    patient.age = age
    patient.ramq = ramq
    patient.full_clean()
    patient.save()


def insert_hospital_identifiers(patient: LegacyPatient, mrns: list[tuple[Site, str, bool]]) -> None:
    """
    Insert legacy hospital identifiers for the patient.

    Args:
        patient: the legacy patient
        mrns: list of MRN tuples consisting of the site, MRN and whether the MRN is active
    """
    hospital_identifiers = [
        LegacyPatientHospitalIdentifier(
            patient=patient,
            mrn=hospital_patient[1],
            is_active=hospital_patient[2],
            hospital_id=hospital_patient[0].acronym,
        )
        for hospital_patient in mrns
    ]
    LegacyPatientHospitalIdentifier.objects.bulk_create(hospital_identifiers)


def create_patient_control(patient: LegacyPatient) -> None:
    """
    Create the patient control for the patient.

    Args:
        patient: the legacy patient
    """
    LegacyPatientControl.objects.create(patient=patient)


def initialize_new_patient(
    patient: Patient,
    mrns: list[tuple[Site, str, bool]],
    self_caregiver: CaregiverProfile | None,
) -> LegacyPatient:
    """
    Initialize a new legacy patient based on an existing patient.

    Creates the legacy patient, inserts the hospital identifiers, and creates the patient control.

    Args:
        patient: the existing patient to initialize a legacy patient instance from
        mrns: list of MRN tuples consisting of the site, MRN and whether the MRN is active
        self_caregiver: the caregiver profile instance if the patient is their own caregiver, otherwise None

    Returns:
        the legacy patient
    """
    date_of_birth = dt.datetime.combine(patient.date_of_birth, dt.time())
    email = self_caregiver.user.email if self_caregiver else ''
    language = LegacyLanguage(self_caregiver.user.language.upper()) if self_caregiver else LegacyLanguage.FRENCH

    legacy_patient = create_patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        sex=SEX_TYPE_MAPPING[patient.sex],
        date_of_birth=timezone.make_aware(date_of_birth),
        email=email,
        language=language,
        ramq=patient.ramq,
        access_level=ACCESS_LEVEL_MAPPING[patient.data_access],
    )

    insert_hospital_identifiers(legacy_patient, mrns)
    create_patient_control(legacy_patient)

    return legacy_patient


def create_user(user_type: LegacyUserType, user_type_id: int, username: str) -> LegacyUsers:
    """
    Create a user with the given properties.

    Args:
        user_type: the type of the user
        user_type_id: the legacy ID of the type of the user (e.g., the patient ID for a patient)
        username: the username of the user

    Returns:
        the created user instance
    """
    user = LegacyUsers(  # noqa: S106
        usertype=user_type,
        usertypesernum=user_type_id,
        username=username,
        password='',
    )

    user.full_clean()
    user.save()

    return user


def update_legacy_user_type(caregiver_legacy_id: int, new_type: LegacyUserType) -> None:
    """
    Update a user's UserType in the legacy Users table.

    Args:
        caregiver_legacy_id: The user's UserSerNum in the legacy Users table.
        new_type: The new UserType to set for the user.
    """
    LegacyUsers.objects.filter(usersernum=caregiver_legacy_id).update(usertype=new_type)


def create_caregiver_user(  # noqa: WPS210 (too many local variables)
    relationship: Relationship,
    username: str,
    language: str,
    email: str,
) -> LegacyUsers:
    """
    Create a user for the caregiver.

    If the relationship the caregiver is created for is a self relationship,
    the patient is expected to be present already.
    In this case, the user record is created with type 'Patient' and pointing to that record.

    Otherwise, a dummy patient is created and the user record created with type 'Caregiver'
    and pointing to the dummy patient.

    Args:
        relationship: the relationship between the caregiver and patient
        username: the username of the caregiver
        language: the language the caregiver selected
        email: the email address of the user account

    Returns:
        the created user
    """
    # the legacy_id is only None if it is not a self relationship
    # otherwise we know that the legacy patient was already added
    user_patient_legacy_id: int = relationship.patient.legacy_id  # type: ignore[assignment]
    user_type = LegacyUserType.PATIENT
    language = LegacyLanguage(language.upper())

    if relationship.type.is_self:
        legacy_patient = LegacyPatient.objects.get(patientsernum=user_patient_legacy_id)

        # add missing user information
        legacy_patient.email = email
        legacy_patient.language = language
        legacy_patient.full_clean()
        legacy_patient.save()
    else:
        caregiver_user = relationship.caregiver.user
        dummy_patient = create_dummy_patient(
            first_name=caregiver_user.first_name,
            last_name=caregiver_user.last_name,
            email=email,
            language=language,
        )
        user_patient_legacy_id = dummy_patient.patientsernum
        user_type = LegacyUserType.CAREGIVER

    return create_user(user_type, user_patient_legacy_id, username)


def change_caregiver_user_to_patient(caregiver_legacy_id: int, patient: Patient) -> None:
    """
    Change an existing legacy caregiver user to a regular patient.

    This assumes that the caregiver is the patient (i.e., has a self relationship).
    The user record's type is updated to Patient.
    In addition, the dummy patient that was previously created is updated.

    Args:
        caregiver_legacy_id: the ID of the caregiver's user record
        patient: the patient instance
    """
    update_legacy_user_type(caregiver_legacy_id, LegacyUserType.PATIENT)
    patient_user = LegacyUsers.objects.get(usersernum=caregiver_legacy_id)
    dummy_patient = LegacyPatient.objects.get(patientsernum=patient_user.usertypesernum)
    sex = SEX_TYPE_MAPPING[patient.sex]
    update_patient(dummy_patient, sex, patient.date_of_birth, patient.ramq)


@transaction.atomic
def create_databank_patient_consent_data(django_patient: Patient) -> bool:  # noqa: WPS210
    """Initialize databank consent information for a newly registered patient.

    Insertions include consent form and related educational material which describes the databank itself.
    Note that this function explicitly does not throw any Errors to avoid affecting registration processes.

    Args:
        django_patient: The patient who has just completed registration

    Returns:
        boolean value indicating success or failure, to help logging in registration endpoint
    """
    try:  # noqa: WPS229
        legacy_patient = LegacyPatient.objects.get(patientsernum=django_patient.legacy_id)

        # Check for the existence of the consent form and educational materials before attempting to insert
        control_records = fetch_databank_control_records(django_patient)
        if not control_records:
            # If a control record can't be found we return without raising to avoid affecting the registration
            return False
        info_sheet, qdb_patient, qdb_questionnaire, questionnaire_control = control_records

        answer_instance = LegacyAnswerQuestionnaire.objects.create(
            questionnaire_id=qdb_questionnaire.id,
            patient_id=qdb_patient.id,
            status=0,
            creation_date=timezone.make_aware(dt.datetime.now()),
            created_by='DJANGO_AUTO_CREATE_DATABANK_CONSENT',
            updated_by='DJANGO_AUTO_CREATE_DATABANK_CONSENT',
        )

        # Link the OpalDB.Questionnaire instance to the QDB.AnswerQuestionnaire instance
        LegacyQuestionnaire.objects.create(
            questionnaire_control_ser_num=questionnaire_control,
            patientsernum=legacy_patient,
            patient_questionnaire_db_ser_num=answer_instance.id,
            completedflag=0,
            date_added=timezone.make_aware(dt.datetime.now()),
        )

        # Create the educational material factsheet
        LegacyEducationalMaterial.objects.create(
            educationalmaterialcontrolsernum=info_sheet,
            patientsernum=legacy_patient,
            readstatus=0,
            date_added=timezone.make_aware(dt.datetime.now()),
        )
    except Exception:
        # Rollback and return empty without raising to avoid affecting registration completion
        transaction.set_rollback(True)
        return False
    return True


def fetch_databank_control_records(django_patient: Patient) -> DatabankControlRecords:
    """Fetch the required control records for databank consent creation.

    If the QuestionnaireDB `SyncPublishQuestionnaire` event has not already populated the
    patient table, then this function will create the patient record linked to the OpalDB.Patient.

    Args:
        django_patient: Django patient instance

    Returns:
        tuple of the found records, or None
    """
    # Retrieve the questionnaire databank consent form controls and infosheet instances
    info_sheet = LegacyEducationalMaterialControl.objects.filter(
        educational_material_type_en='Factsheet',
        publish_flag=1,
        name_en__icontains='Consent Factsheet - QSCC Databank',
    ).first()
    qdb_questionnaire = QDB_LegacyQuestionnaire.objects.filter(
        title__content__icontains='QSCC Databank Information',
        title__language_id=2,
    ).first()
    questionnaire_control = LegacyQuestionnaireControl.objects.filter(
        questionnaire_name_en__icontains='QSCC Databank Information',
        publish_flag=1,
    ).first()

    # If the questionnaireDB patient population event hasnt run yet, create the patient record
    qdb_patient, created = LegacyQuestionnairePatient.objects.get_or_create(
        external_id=django_patient.legacy_id,
        defaults={
            'hospital_id': -1,
            'creation_date': timezone.make_aware(dt.datetime.now()),
            'created_by': 'DJANGO_AUTO_CREATE_DATABANK_CONSENT',
            'updated_by': 'DJANGO_AUTO_CREATE_DATABANK_CONSENT',
            'deleted_by': '',
        },
    )
    # Exit if we fail to locate the consent form or the educational material in the db
    if not (qdb_questionnaire and info_sheet and questionnaire_control):
        return None
    return (info_sheet, qdb_patient, qdb_questionnaire, questionnaire_control)


@transaction.atomic
def get_questionnaire_data(patient: Patient) -> list[QuestionnaireData]:
    """
    Handle sync check for the questionnaire respondents.

    Args:
        patient: patient for data

    Raises:
        OperationalError: if there are deviations
        ValueError: value error given as arguments

    Returns:
        list of the questionnaireData

    """
    if patient.legacy_id:
        external_patient_id = patient.legacy_id
    else:
        raise ValueError('The patient has no legacy id.')

    try:
        query_result = _fetch_questionnaires_from_db(external_patient_id)
    except OperationalError as exc:
        raise OperationalError(f'Error fetching questionnaires: {exc}')

    try:
        data_list = _parse_query_result(query_result)
    except ValueError as exc:  # noqa: WPS440
        raise ValueError(f'Error parsing questionnaires: {exc}')
    return _process_questionnaire_data(data_list)


def _fetch_questionnaires_from_db(
    legacy_patient_id: int,
) -> list[dict[str, Any] | list[dict[str, Any]]]:  # noqa: WPS221
    """Fetch completed questionnaires data from the database.

    Args:
        legacy_patient_id: patient's legacy id

    Returns:
        the result of the query
    """
    with connections['questionnaire'].cursor() as cursor:
        cursor.callproc(
            'getCompletedQuestionnairesList',
            [legacy_patient_id, 1, 'FR'],
        )
        return [
            json.loads(row[0]) for row in cursor.fetchall()
        ]


def _parse_query_result(
    query_result: list[dict[str, Any] | list[dict[str, Any]]],  # noqa: WPS221
) -> list[dict[str, Any]]:
    """Parse the raw query result into a structured list of dictionaries.

    This function processes each row in the query result, expecting JSON data in the first column
    (`row[0]`). The JSON is deserialized, and the resulting data is added to a list.

    Args:
        query_result: raw query results, each tuple represents a database row

    Raises:
        ValueError: if the JSON data cannot be deserialized

    Returns:
        structured list of dictonaries representing the query
    """
    data_list = []
    for parsed_data in query_result:
        if isinstance(parsed_data, dict):
            data_list.append(parsed_data)
        elif isinstance(parsed_data, list):
            data_list.extend(parsed_data)
        else:
            raise ValueError(
                f'Expected parsed data to be a dict or list of dicts, got {type(parsed_data)}.',
            )
    return data_list


def _process_questionnaire_data(parsed_data_list: list[dict[str, Any]]) -> list[QuestionnaireData]:
    """Process parsed questionnaire data into QuestionnaireData objects.

    Args:
        parsed_data_list: parsed data list of the questionnaire

    Raises:
        ValueError: if the questionnaire format is wrong

    Returns:
        complete answered questionnaire data list of the patient
    """
    questionnaire_data_list = []

    for data in parsed_data_list:
        if 'questions' not in data:
            raise ValueError(f'Unexpected data format: {data!r}')
        questions = _process_questions(data['questions'])
        questionnaire_data_list.append(
            QuestionnaireData(
                questionnaire_id=data['questionnaire_id'],
                questionnaire_title=data['questionnaire_nickname'],
                last_updated=datetime.fromisoformat(data['last_updated']),
                questions=questions,
            ),
        )

    return questionnaire_data_list


def _process_questions(questions_data: list[dict[str, Any]]) -> list[Question]:
    """Process question data into Question objects.

    Args:
        questions_data: unprocessed questions data associated with the questionnaire

    Raises:
        CommandError: if the question format is wrong

    Returns:
        list of questions associated with the questionnaire
    """
    questions = []

    for que in questions_data:

        answers = que.get('values') or []
        if not isinstance(answers, list):
            raise CommandError(f"Invalid 'values' format for question: {que}")

        questions.append(
            Question(
                question_text=que['question_text'],
                question_label=que['question_label'],
                question_type_id=que['question_type_id'],
                position=que['position'],
                min_value=que['min_value'],
                max_value=que['max_value'],
                polarity=que['polarity'],
                section_id=que['section_id'],
                answers=[
                    (
                        datetime.fromisoformat(answer[0]),
                        str(answer[1]),
                    ) for answer in answers
                ],
            ),
        )

    return questions


def generate_questionnaire_report(
    patient: Patient,
    questionnaire_data_list: list[QuestionnaireData],
) -> bytearray:
    """Generate the questionnaire PDF report by calling the PDF generator for Questionnaires.

    Args:
        patient: patient instance for whom a new PDF questionnaire report being generated
        questionnaire_data_list: list of questionnaireData required to generate the PDF report

    Returns:
        bytearray: the generated questionnaire report
    """
    return generate_pdf(
        institution=InstitutionData(
            institution_logo_path=Path(Institution.objects.get().logo.path),
        ),
        patient=PatientData(
            patient_first_name=patient.first_name,
            patient_last_name=patient.last_name,
            patient_date_of_birth=patient.date_of_birth,
            patient_ramq=patient.ramq,
            patient_sites_and_mrns=list(
                patient.hospital_patients.all().annotate(
                    site_code=models.F('site__acronym'),
                ).values('mrn', 'site_code'),
            ),
        ),
        questionnaires=questionnaire_data_list,
    )
