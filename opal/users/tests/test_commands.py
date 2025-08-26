# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.core.management.base import CommandError

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.caregivers import models as caregiver_models
from opal.core.test_utils import CommandTestMixin
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.users import models as user_models

pytestmark = pytest.mark.django_db()


class TestAccountDeletion(CommandTestMixin):
    """Test class to group the `delete_account` command tests."""

    def test_delete_missing_ramq(self) -> None:
        """Ensure that the ramq argument is required."""
        with pytest.raises(CommandError, match='the following arguments are required: ramq'):
            self._call_command('delete_account')

    @pytest.mark.django_db(databases=['default'])
    def test_delete_user_with_sccuess(self) -> None:
        """Ensure the input user is deleted successfully with the backup generated."""
        patient = patient_factories.Patient.create(ramq='TEST')
        caregiver = caregiver_factories.CaregiverProfile.create()
        relationship = patient_factories.RelationshipType.create(name='Self')
        patient_factories.Relationship.create(patient=patient, caregiver=caregiver, type=relationship)
        caregiver_factories.SecurityAnswer.create(user=caregiver)
        caregiver_factories.Device.create(caregiver=caregiver)
        patient_factories.HospitalPatient.create(patient=patient)

        assert patient_models.Patient.objects.count() == 1
        assert caregiver_models.CaregiverProfile.objects.count() == 1
        assert user_models.User.objects.count() == 1
        assert patient_models.Relationship.objects.count() == 1
        assert caregiver_models.SecurityAnswer.objects.count() == 1
        assert caregiver_models.Device.objects.count() == 1
        assert patient_models.HospitalPatient.objects.count() == 1

        stdout, _stderr = self._call_command('delete_account', 'TEST')

        assert 'The account deletion is completed!' in stdout
        assert patient_models.Patient.objects.count() == 0
        assert caregiver_models.CaregiverProfile.objects.count() == 0
        assert user_models.User.objects.count() == 0
        assert patient_models.Relationship.objects.count() == 0
        assert caregiver_models.SecurityAnswer.objects.count() == 0
        assert caregiver_models.Device.objects.count() == 0
        assert patient_models.HospitalPatient.objects.count() == 0

    def test_delete_nonexistent_patient(self) -> None:
        """Ensure the error message is returned when the nonexistent ramq is given."""
        stdout, stderr = self._call_command('delete_account', 'TEST')

        assert stdout == ''
        assert stderr == 'Patient not found.\n'

    def test_delete_nonexistent_caregiver(self) -> None:
        """Ensure the error message is returned when the given patient is not an Opal user."""
        patient_factories.Patient.create(ramq='TEST')
        stdout, stderr = self._call_command('delete_account', 'TEST')

        assert stdout == ''
        assert stderr == 'The given patient is not an Opal user.\n'
