import pytest

from opal.patients import factories as patient_factory
from opal.patients.models import HospitalPatient

pytestmark = pytest.mark.django_db


def test_get_hospital_patient_by_site_mrn() -> None:
    """Test the query to get a `HospitalPatient` record filtered by given site code and MRN."""
    hospital_patient = patient_factory.HospitalPatient()
    query_result = HospitalPatient.objects.get_hospital_patient_by_site_mrn(
        site=hospital_patient.site.code,
        mrn=hospital_patient.mrn,
    )

    assert query_result[0].patient.legacy_id == hospital_patient.patient.legacy_id
    assert query_result[0].mrn == hospital_patient.mrn
    assert query_result[0].site.code == hospital_patient.site.code
    assert query_result[0].site.name == hospital_patient.site.name
    assert query_result[0].is_active is True
