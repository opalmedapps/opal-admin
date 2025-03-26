import datetime as dt

from django.utils import timezone

import pytest
from dateutil.relativedelta import relativedelta

from opal.caregivers import factories as caregiver_factories
from opal.hospital_settings import factories as hospital_factories
from opal.legacy import factories, models
from opal.legacy import utils as legacy_utils
from opal.legacy_questionnaires import factories as questionnaire_factories
from opal.legacy_questionnaires import models as questionnaire_models
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipType

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
    legacy_qdb_patient = questionnaire_factories.LegacyPatientFactory(external_id=django_patient.legacy_id)
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
    # Setup patient records
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

    qdb_patient = questionnaire_models.LegacyPatient.objects.get(
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
