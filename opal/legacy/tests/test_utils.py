import pytest

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


def test_update_legacy_user_type() -> None:
    """Ensure that a legacy user's type can be updated."""
    legacy_user = factories.LegacyUserFactory(usertype='Caregiver')
    legacy_utils.update_legacy_user_type(legacy_user.usersernum, 'Patient')
    legacy_user.refresh_from_db()

    assert legacy_user.usertype == 'Patient'


def test_insert_hospital_identifiers() -> None:
    """The patient's hospital identifiers are added for the legacy patient."""
    patient = patient_factories.Patient()
    patient_factories.HospitalPatient(patient=patient, mrn='9999995', site__code='RVH')
    patient_factories.HospitalPatient(patient=patient, mrn='7654321', site__code='MGH')
    patient_factories.HospitalPatient(patient=patient, mrn='1234567', site__code='MCH', is_active=False)

    legacy_patient = factories.LegacyPatientFactory(patientsernum=patient.legacy_id)

    factories.LegacyHospitalIdentifierTypeFactory(code='RVH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MGH')
    factories.LegacyHospitalIdentifierTypeFactory(code='MCH')

    legacy_utils.insert_hospital_identifiers(patient.legacy_id)

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
    factories.LegacyPatientFactory(patientsernum=321)

    legacy_utils.create_patient_control(321)

    assert models.LegacyPatientControl.objects.count() == 1
    assert models.LegacyPatientControl.objects.get().patient_id == 321
