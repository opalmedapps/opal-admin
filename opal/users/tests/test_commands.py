# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

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

    def test_delete_missing_email(self) -> None:
        """Ensure that the email argument is required."""
        with pytest.raises(CommandError, match='the following arguments are required: email'):
            self._call_command('delete_account')

    @pytest.mark.django_db(databases=['default'])
    def test_delete_user_with_success(self) -> None:
        """Ensure the input user is deleted successfully with the backup generated."""
        patient = patient_factories.Patient.create()
        caregiver = caregiver_factories.CaregiverProfile.create(user__email='test@test.com')
        relationship = patient_factories.RelationshipType.create(role_type=patient_models.RoleType.SELF)
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

        stdout, _stderr = self._call_command('delete_account', 'test@test.com')
        # User was deleted
        assert stdout != ''
        assert patient_models.Patient.objects.count() == 0
        assert caregiver_models.CaregiverProfile.objects.count() == 0
        assert user_models.User.objects.count() == 0
        assert patient_models.Relationship.objects.count() == 0
        assert caregiver_models.SecurityAnswer.objects.count() == 0
        assert caregiver_models.Device.objects.count() == 0
        assert patient_models.HospitalPatient.objects.count() == 0

    def test_delete_nonexistent_user(self) -> None:
        """Ensure the error message is returned when the nonexistent user is given."""
        stdout, stderr = self._call_command('delete_account', 'test@test.com')

        assert stdout == ''
        assert stderr == 'User not found.\n'

    def test_delete_nonexistent_self_relationship(self) -> None:
        """Ensure the error message is returned when the given user doesn't have a self relationship."""
        patient = patient_factories.Patient.create()
        caregiver = caregiver_factories.CaregiverProfile.create(user__email='test@test.com')
        relationship_type = patient_factories.RelationshipType.create()
        patient_factories.Relationship.create(patient=patient, caregiver=caregiver, type=relationship_type)

        assert patient_models.Patient.objects.count() == 1
        assert caregiver_models.CaregiverProfile.objects.count() == 1
        assert user_models.User.objects.count() == 1
        assert patient_models.Relationship.objects.count() == 1
        stdout, _stderr = self._call_command('delete_account', 'test@test.com')
        # Only user was deleted
        assert stdout != ''
        assert patient_models.Patient.objects.count() == 1
        assert caregiver_models.CaregiverProfile.objects.count() == 0
        assert user_models.User.objects.count() == 0
        assert patient_models.Relationship.objects.count() == 0


class TestAccountRecover(CommandTestMixin):
    """Test class to group the `delete_account` command tests."""

    def test_recover_missing_file_path(self) -> None:
        """Ensure that the file_path argument is required."""
        with pytest.raises(CommandError, match='the following arguments are required: file_path'):
            self._call_command('recover_account')

    def test_recover_user_with_success(self) -> None:
        """Ensure the input user is recovered successfully using the backup data."""
        patient = patient_factories.Patient.create()
        caregiver = caregiver_factories.CaregiverProfile.create(user__email='test@test.com')
        relationship = patient_factories.RelationshipType.create(role_type=patient_models.RoleType.SELF)
        patient_factories.Relationship.create(patient=patient, caregiver=caregiver, type=relationship)
        caregiver_factories.SecurityAnswer.create(user=caregiver)
        caregiver_factories.Device.create(caregiver=caregiver)
        patient_factories.HospitalPatient.create(patient=patient)

        stdout, _stderr = self._call_command('delete_account', 'test@test.com')
        # User was deleted
        assert patient_models.Patient.objects.count() == 0
        assert caregiver_models.CaregiverProfile.objects.count() == 0
        assert user_models.User.objects.count() == 0
        assert patient_models.Relationship.objects.count() == 0
        assert caregiver_models.SecurityAnswer.objects.count() == 0
        assert caregiver_models.Device.objects.count() == 0
        assert patient_models.HospitalPatient.objects.count() == 0
        with Path('test.json').open('w', encoding='utf-8') as file:
            file.write(stdout)
        stdout, _stderr = self._call_command('recover_account', 'test.json')
        assert stdout == 'Data successfully recovered! Please delete the backup file.\n'
        assert patient_models.Patient.objects.count() == 1
        assert caregiver_models.CaregiverProfile.objects.count() == 1
        assert user_models.User.objects.count() == 1
        assert patient_models.Relationship.objects.count() == 1
        assert caregiver_models.SecurityAnswer.objects.count() == 1
        assert caregiver_models.Device.objects.count() == 1
        assert patient_models.HospitalPatient.objects.count() == 1
        Path.unlink(Path('test.json'))
