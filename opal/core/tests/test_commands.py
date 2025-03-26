import pytest

from opal.caregivers.models import CaregiverProfile
from opal.core.test_utils import CommandTestMixin
from opal.hospital_settings.models import Institution, Site
from opal.patients import factories
from opal.patients.models import HospitalPatient, Patient, Relationship
from opal.users.models import Caregiver

pytestmark = pytest.mark.django_db()


class TestInsertTestData(CommandTestMixin):
    """Test class to group the `insert_test_data` command tests."""

    def test_insert(self) -> None:
        """Ensure that test data is inserting when there is no existing data."""
        stdout, _stderr = self._call_command('insert_test_data')

        assert Institution.objects.count() == 1
        assert Site.objects.count() == 4
        assert Patient.objects.count() == 5
        assert HospitalPatient.objects.count() == 6
        assert CaregiverProfile.objects.count() == 3
        assert Relationship.objects.count() == 7
        assert stdout == 'Test data successfully created\n'

    def test_insert_existing_data_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The insertion can be cancelled when there is already data."""
        monkeypatch.setattr('builtins.input', lambda _: 'foo')
        relationship = factories.Relationship()

        stdout, _stderr = self._call_command('insert_test_data')

        assert stdout == 'Test data insertion cancelled\n'
        relationship.refresh_from_db()

    def test_insert_existing_data_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The existing data is deleted when confirmed and new data added."""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        relationship = factories.Relationship()
        hospital_patient = factories.HospitalPatient()

        institution = Institution.objects.get()
        site = Site.objects.get()
        patient = Patient.objects.get()
        caregiver_profile = CaregiverProfile.objects.get()
        caregiver = Caregiver.objects.get()

        stdout, _stderr = self._call_command('insert_test_data')

        assert 'Existing test data deleted' in stdout
        assert 'Test data successfully created' in stdout

        # old data was deleted
        assert not Relationship.objects.filter(pk=relationship.pk).exists()
        assert not HospitalPatient.objects.filter(pk=hospital_patient.pk).exists()
        assert not Relationship.objects.filter(pk=institution.pk).exists()
        assert not Relationship.objects.filter(pk=site.pk).exists()
        assert not Relationship.objects.filter(pk=patient.pk).exists()
        assert not Relationship.objects.filter(pk=caregiver_profile.pk).exists()
        assert not Relationship.objects.filter(pk=caregiver.pk).exists()

        # new data was created
        assert Institution.objects.count() == 1
        assert Site.objects.count() == 4
        assert Patient.objects.count() == 5
        assert HospitalPatient.objects.count() == 6
        assert CaregiverProfile.objects.count() == 3
        assert Relationship.objects.count() == 7
