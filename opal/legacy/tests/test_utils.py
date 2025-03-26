import datetime as dt

from django.utils import timezone

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.hospital_settings import factories as hospital_factories
from opal.legacy import factories, models
from opal.legacy import utils as legacy_utils
from opal.patients import factories as patient_factories

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
        timezone.make_aware(dt.datetime(1986, 10, 5)),
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
    legacy_utils.update_patient(legacy_patient, models.LegacySexType.OTHER, date_of_birth, 'SIMB08032999')

    legacy_patient.refresh_from_db()

    assert legacy_patient.sex == models.LegacySexType.OTHER
    assert legacy_patient.date_of_birth == date_of_birth
    assert legacy_patient.age == 15
    assert legacy_patient.ramq == 'SIMB08032999'


def test_insert_hospital_identifiers() -> None:
    """The patient's hospital identifiers are added for the legacy patient."""
    rvh = hospital_factories.Site(acronym='RVH', acronym_fr='RVHF')
    mgh = hospital_factories.Site(acronym='MGH', acronym_fr='MGHF')
    mch = hospital_factories.Site(acronym='MCH', acronym_fr='MCHF')

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
            (hospital_factories.Site(acronym='RVH', acronym='RVHF'), '9999995', True),
            (hospital_factories.Site(acronym='MGH', acronym='MGHF'), '7654321', True),
            (hospital_factories.Site(acronym='MCH', acronym='MCHF'), '1234567', False),
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


def test_update_legacy_user_type() -> None:
    """Ensure that a legacy user's type can be updated."""
    legacy_user = factories.LegacyUserFactory(usertype=models.LegacyUserType.CAREGIVER)
    legacy_utils.update_legacy_user_type(legacy_user.usersernum, models.LegacyUserType.PATIENT)
    legacy_user.refresh_from_db()

    assert legacy_user.usertype == models.LegacyUserType.PATIENT
