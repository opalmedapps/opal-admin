# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import uuid
from datetime import date, datetime
from http import HTTPStatus

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connections
from django.utils import timezone

import pytest
import requests
from pytest_django import DjangoDbBlocker
from pytest_mock.plugin import MockerFixture

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import SecurityAnswer, SecurityQuestion
from opal.core.test_utils import CommandTestMixin, RequestMockerTest
from opal.hospital_settings import factories as hospital_settings_factories
from opal.legacy import factories as legacy_factories
from opal.legacy import models as legacy_models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity
from opal.users import factories as user_factories
from opal.users.models import ClinicalStaff

from ..management.commands import migrate_caregivers

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestSecurityQuestionsMigration(CommandTestMixin):
    """Test class for security questions migration."""

    def test_import_fails_question_exists(self) -> None:
        """Test import fails due to security question already exists."""
        legacy_factories.LegacySecurityQuestionFactory.create()
        caregiver_factories.SecurityQuestion.create(title_en='What is the name of your first pet?')
        message, error = self._call_command('migrate_securityquestions')
        question = SecurityQuestion.objects.all()
        assert len(question) != 2
        assert message == (
            'Security question sernum: 1, title: What is the name of your first pet? exists already, skipping\n'
        )
        assert error == ''

    def test_import_succeeds(self) -> None:
        """Test import a security question successfully."""
        legacy_factories.LegacySecurityQuestionFactory.create()
        message, error = self._call_command('migrate_securityquestions')
        question = SecurityQuestion.objects.all()
        assert len(question) == 1
        assert question[0].title_en == 'What is the name of your first pet?'  # type: ignore[attr-defined]
        assert question[0].title_fr == 'Quel est le nom de votre premier animal de compagnie?'  # type: ignore[attr-defined]
        assert message == ('Imported security question, sernum: 1, title: What is the name of your first pet?\n')
        assert error == ''


class TestSecurityAnswersMigration(CommandTestMixin):
    """Test class for security answers migration."""

    def test_import_fails_legacy_user_not_exists(self) -> None:
        """Test import fails due to legacy user not exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert not answers
        assert message == 'Migrated 0 out of 1 security answers\n'
        assert error == (
            'Legacy user does not exist, usertypesernum: 99\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_multiple_legacy_user(self) -> None:
        """Test import fails due to multiple legacy users."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum)
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum)
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert not answers
        assert message == 'Migrated 0 out of 1 security answers\n'
        assert error == (
            'Found more than one related legacy users, usertypesernum: 99\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_user_not_exists(self) -> None:
        """Test import fails due to user not exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum, username='no_name')
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert not answers
        assert message == 'Migrated 0 out of 1 security answers\n'
        assert error == (
            'User does not exist, username: no_name\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_no_caregiver_profile(self) -> None:
        """Test import fails due to caregiver profile not exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum, username='username')
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)
        user_factories.User.create(username='username')

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert not answers
        assert message == 'Migrated 0 out of 1 security answers\n'
        assert error == ('Security answer import failed, sernum: 1, details: Caregiver does not exist\n')

    def test_import_fails_security_answer_exists(self) -> None:
        """Test import fails due to security answer already exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum, username='username')
        legacy_answer = legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)
        user = user_factories.User.create(username='username')
        caregiver = caregiver_factories.CaregiverProfile.create(user=user)
        caregiver_factories.SecurityAnswer.create(
            user=caregiver,
            question=legacy_answer.securityquestionsernum.questiontext_en,
            answer=legacy_answer.answertext,
        )

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert len(answers) == 1
        assert 'Security answer already exists, sernum: 1' in message
        assert 'Migrated 0 out of 1 security answers' in message
        assert error == ''

    def test_import_succeeds(self) -> None:
        """Test import succeeds."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum, username='username')
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)
        user = user_factories.User.create(username='username', language='en')
        caregiver_factories.CaregiverProfile.create(user=user)

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert len(answers) == 1
        assert answers[0].question == 'What is the name of your first pet?'
        assert answers[0].answer == 'bird'
        assert message == 'Migrated 1 out of 1 security answers\n'
        assert error == ''

    def test_import_question_fr_by_user_language(self) -> None:
        """Test import question language by user language."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyUserFactory.create(usertypesernum=legacy_patient.patientsernum, username='username')
        legacy_factories.LegacySecurityAnswerFactory.create(patient=legacy_patient)
        user = user_factories.User.create(username='username', language='fr')
        caregiver_factories.CaregiverProfile.create(user=user)

        message, error = self._call_command('migrate_securityanswers')

        answers = SecurityAnswer.objects.all()
        assert len(answers) == 1
        assert answers[0].question == 'Quel est le nom de votre premier animal de compagnie?'
        assert answers[0].answer == 'bird'
        assert message == 'Migrated 1 out of 1 security answers\n'
        assert error == ''


class TestPatientAndPatientIdentifierMigration(CommandTestMixin):
    """Test class for security answers migration."""

    def test_import_patient(self) -> None:
        """The patient is imported with the correct data."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()

        self._call_command('migrate_patients')

        patient = patient_models.Patient.objects.get(legacy_id=51)

        assert patient.date_of_birth == date(2018, 1, 1)
        assert patient.sex == patient_models.Patient.SexType.MALE
        assert patient.first_name == legacy_patient.first_name
        assert patient.last_name == legacy_patient.last_name
        assert patient.ramq == legacy_patient.ramq

    def test_import_deceased_patient(self) -> None:
        """The patient is imported with the correct data."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(
            death_date=datetime(2118, 1, 1, tzinfo=timezone.get_current_timezone()),
        )

        self._call_command('migrate_patients')

        patient = patient_models.Patient.objects.get(legacy_id=51)

        assert patient.date_of_birth == date(2018, 1, 1)
        assert patient.date_of_death == datetime(2118, 1, 1, tzinfo=timezone.get_current_timezone())
        assert patient.sex == patient_models.Patient.SexType.MALE
        assert patient.first_name == legacy_patient.first_name
        assert patient.last_name == legacy_patient.last_name
        assert patient.ramq == legacy_patient.ramq

    @pytest.mark.parametrize(
        ('data_access', 'legacy_data_access'),
        [
            (patient_models.Patient.DataAccessType.ALL, '3'),
            (patient_models.Patient.DataAccessType.NEED_TO_KNOW, '1'),
        ],
    )
    def test_import_patient_data_access(
        self,
        data_access: patient_models.Patient.DataAccessType,
        legacy_data_access: str,
    ) -> None:
        """The patient is imported with the data access level."""
        legacy_factories.LegacyPatientFactory.create(access_level=legacy_data_access)

        self._call_command('migrate_patients')

        patient = patient_models.Patient.objects.get(legacy_id=51)
        assert patient.data_access == data_access

    def test_import_legacy_patient_not_exist_fail(self) -> None:
        """Test import fails no legacy patient exists."""
        _message, error = self._call_command('migrate_patients')

        assert error.strip() == ('No legacy patients exist')

    def test_import_legacy_patient_already_exist_fail(self) -> None:
        """Test import fails patient already exists."""
        legacy_factories.LegacyPatientFactory.create(patientsernum=51)
        patient_factories.Patient.create(legacy_id=51)
        message, _error = self._call_command('migrate_patients')
        assert 'Patient with legacy_id: 51 already exists, skipping\n' in message

    def test_import_patient_pass_no_identifier_exists(self) -> None:
        """Test import pass for patient fail for patient identifier."""
        legacy_factories.LegacyPatientFactory.create()
        message, _error = self._call_command('migrate_patients')
        assert 'No hospital patient identifiers for patient with legacy_id: 51 exists, skipping\n' in message

    def test_import_patient_patientidentifier_pass(self) -> None:
        """Test import pass for patient and patient identifier."""
        legacy_factories.LegacyPatientFactory.create()
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create()
        patient_factories.Patient.create()
        hospital_settings_factories.Site.create(acronym='RVH')

        message, _error = self._call_command('migrate_patients')

        assert 'Number of imported patients is: 1 (out of 1)\n' in message

    def test_import_pass_patientidentifier_only(self) -> None:
        """Test import fail for patient and pass patient identifier."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=10)
        patient_factories.Patient.create(legacy_id=10)
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(patient=legacy_patient)
        hospital_settings_factories.Site.create(acronym='RVH')

        message, _error = self._call_command('migrate_patients')

        assert 'Patient with legacy_id: 10 already exists, skipping\n' in message
        assert 'Number of imported patients is: 0 (out of 1)\n' in message

    def test_import_pass_patient_only(self) -> None:
        """Test import pass for patient and fail patient identifier already exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        patient = patient_factories.Patient.create(legacy_id=99)
        hospital = legacy_factories.LegacyHospitalIdentifierTypeFactory.create(code='TEST')
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(
            hospital=hospital,
            patient=legacy_patient,
            mrn='9999996',
        )
        site = hospital_settings_factories.Site.create(acronym='TEST')
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient,
            mrn='9999996',
        )

        message, _error = self._call_command('migrate_patients')

        assert 'Patient with legacy_id: 99 already exists, skipping\n' in message
        assert 'Patient identifier legacy_id: 99, mrn: 9999996 already exists, skipping\n' in message
        assert 'Number of imported patients is: 0 (out of 1)\n' in message

    def test_import_failure_multiple_mrns_at_same_site(self) -> None:
        """Test import fail for patient with multiple MRNs at the same site."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=10)
        patient_factories.Patient.create(legacy_id=10)
        hospital = legacy_factories.LegacyHospitalIdentifierTypeFactory.create(code='TEST')
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(
            hospital=hospital,
            patient=legacy_patient,
            mrn='9999996',
        )
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(
            hospital=hospital,
            patient=legacy_patient,
            mrn='9999997',
        )
        hospital_settings_factories.Site.create(acronym='TEST')

        message, error = self._call_command('migrate_patients')

        assert 'Patient with legacy_id: 10 already exists, skipping\n' in message
        assert 'Number of imported patients is: 0 (out of 1)\n' in message
        assert error == (
            'Cannot import patient hospital identifier for patient (legacy ID: 10, MRN: 9999997),'
            + ' already has an MRN at the same site (TEST)\n'
        )


class TestUsersCaregiversMigration(CommandTestMixin):
    """Test class for users and caregivers migrations from legacy DB."""

    def test_import_user_caregiver_no_legacy_users(self) -> None:
        """Test import fails no legacy users exist."""
        message, _error = self._call_command('migrate_caregivers')

        assert 'Number of imported caregivers is: 0' in message

    def test_import_user_caregiver_no_patient_exist(self) -> None:
        """Test import fails, a corresponding patient in new backend does not exist."""
        legacy_factories.LegacyUserFactory.create(usertypesernum=99)

        _message, error = self._call_command('migrate_caregivers')

        assert 'Patient with sernum: 99, does not exist, skipping.\n' in error

    def test_import_user_caregiver_already_exist(self) -> None:
        """Test import fails, caregiver profile has already been migrated."""
        legacy_user = legacy_factories.LegacyUserFactory.create(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient.create(legacy_id=99)
        patient_factories.CaregiverProfile.create(
            legacy_id=legacy_user.usersernum,
            # use same name to satisfy self relationship constraint
            user__first_name=patient.first_name,
            user__last_name=patient.last_name,
        )

        message, _error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0 (out of 1)\n' in message

    def test_import_user_caregiver_exists_relation(self) -> None:
        """Test import relation fails, relation already exists."""
        legacy_factories.LegacyUserFactory.create(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient.create(legacy_id=99)
        relationship_type = patient_models.RelationshipType.objects.self_type()
        caregiver = patient_factories.CaregiverProfile.create(legacy_id=55)
        patient_factories.Relationship.create(
            patient=patient,
            caregiver=caregiver,
            type=relationship_type,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        message, _error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0 (out of 1)\n' in message
        assert 'Self relationship for patient with legacy_id: 99 already exists.\n' in message

    def test_import_user_caregiver_no_relation(self) -> None:
        """Test import pass for relationship for already migrated caregiver."""
        legacy_user = legacy_factories.LegacyUserFactory.create(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient.create(legacy_id=99)
        patient_factories.CaregiverProfile.create(
            legacy_id=legacy_user.usersernum,
            # use same name to satisfy self relationship constraint
            user__first_name=patient.first_name,
            user__last_name=patient.last_name,
        )

        message, _error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0 (out of 1)\n' in message

    def test_import_new_user_caregiver_no_relation(self) -> None:
        """Test import pass for caregiver profile and relationship."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        legacy_factories.LegacyUserFactory.create(usersernum=55, usertypesernum=99)
        patient_factories.Patient.create(
            legacy_id=99,
            first_name=legacy_patient.first_name,
            last_name=legacy_patient.last_name,
        )
        message, _error = self._call_command('migrate_caregivers')

        assert 'Number of imported caregivers is: 1 (out of 1)\n' in message

    def test_import_new_user_caregiver_with_relation(self) -> None:
        """Test import pass for multiple caregiver profiles and their relations."""
        legacy_patient1 = legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        legacy_patient2 = legacy_factories.LegacyPatientFactory.create(patientsernum=100)
        legacy_factories.LegacyUserFactory.create(usersernum=55, usertypesernum=99, username='test1')
        legacy_factories.LegacyUserFactory.create(usersernum=56, usertypesernum=100, username='test2')
        patient_factories.Patient.create(
            legacy_id=99,
            first_name=legacy_patient1.first_name,
            last_name=legacy_patient1.last_name,
            ramq='RAMQ12345678',
        )
        patient_factories.Patient.create(
            legacy_id=100,
            first_name=legacy_patient2.first_name,
            last_name=legacy_patient2.last_name,
        )
        message, _error = self._call_command('migrate_caregivers')

        assert 'Number of imported caregivers is: 2 (out of 2)\n' in message

    def test_import_new_user_phone_number_converted(self) -> None:
        """Ensure that the phone number is correctly converted to a string and prefixed with the country code."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(tel_num=514123456789)
        legacy_user = legacy_factories.LegacyUserFactory.create()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert profile.user.phone_number == '+1514123456789'

    def test_import_new_user_phone_number_missing(self) -> None:
        """Ensure that a legacy patient without a phone number is correctly migrated."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create(tel_num=None)
        legacy_user = legacy_factories.LegacyUserFactory.create()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert profile.user.phone_number == ''

    def test_import_user_caregiver_has_unusable_password(self) -> None:
        """Ensure that migrated caregivers are assigned unusable passwords (since passwords aren't currently saved)."""
        legacy_patient = legacy_factories.LegacyPatientFactory.create()
        legacy_user = legacy_factories.LegacyUserFactory.create()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert not profile.user.has_usable_password()


class TestPatientsDeviationsCommand(CommandTestMixin):
    """Test class for the custom command that detects `Patient` model/tables deviations."""

    def test_no_deviations(self) -> None:
        """Ensure the command does not fail if there are no patient and caregiver records."""
        message, _error = self._call_command('find_deviations')
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def test_deviations_uneven_patient_records(self) -> None:
        """Ensure the command handles the cases when "Patient" model/tables have uneven number of records."""
        user_factories.Caregiver.create(first_name='Marge', last_name='Simpson')
        patient_factories.Patient.create(legacy_id=99, first_name='Marge', last_name='Simpson', ramq='RAMQ12345678')
        legacy_factories.LegacyUserFactory.create(usersernum=99, usertypesernum=99)
        legacy_factories.LegacyUserFactory.create(usersernum=100, usertypesernum=100)
        legacy_factories.LegacyPatientControlFactory.create(
            patient=legacy_factories.LegacyPatientFactory.create(patientsernum=99),
        )
        legacy_factories.LegacyPatientControlFactory.create(
            patient=legacy_factories.LegacyPatientFactory.create(patientsernum=100),
        )

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        assert (
            'found deviations between opal.patients_patient Django model'
            + ' and OpalDB.Patient(UserType="Patient") legacy table!!!'
        ) in error
        assert (
            'The number of records in "opal.patients_patient"'
            + ' and "OpalDB.Patient(UserType="Patient")" tables does not match!'
        ) in error
        assert 'opal.patients_patient: 1' in error
        assert 'OpalDB.Patient(UserType="Patient"): 2' in error

    def test_patient_records_deviations(self) -> None:
        """Ensure the command detects the deviations in the "Patient" model and tables."""
        # Create legacy patient
        legacy_factories.LegacyUserFactory.create(usertypesernum=51)
        legacy_factories.LegacyPatientControlFactory.create(
            patient=legacy_factories.LegacyPatientFactory.create(patientsernum=51),
        )

        # Create Django patient
        patient_factories.CaregiverProfile.create(
            user=user_factories.Caregiver.create(
                first_name='Marge',
                last_name='Simpson',
                email='test@test.com',
                username='username',
            ),
            legacy_id=51,
        )
        patient_factories.Patient.create(legacy_id=51)

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        assert (
            'found deviations between opal.patients_patient Django model'
            + ' and OpalDB.Patient(UserType="Patient") legacy table!!!'
        ) in error

        assert 'opal.patients_patient  <===>  OpalDB.Patient(UserType="Patient"):' in error
        assert "(51, '', 'Marge', 'Simpson', '1999-01-01', 'M', 'ALL', None" in error
        assert ("(51, 'SIMM18510198', 'Marge', 'Simpson', '2018-01-01', 'M', 'ALL', None)") in error

    def test_deviations_uneven_hospital_patient_records(self) -> None:
        """Ensure the command handles the cases when "HospitalPatient" model/tables have uneven number of records."""
        legacy_factories.LegacyUserFactory.create(usersernum=99, usertypesernum=99)
        legacy_factories.LegacyUserFactory.create(usersernum=98, usertypesernum=98)
        first_patient = patient_factories.Patient.create(ramq='RAMQ12345678', legacy_id=99)
        second_patient = patient_factories.Patient.create(ramq='RAMQ87654321', legacy_id=98)
        patient_factories.HospitalPatient.create(patient=first_patient)
        patient_factories.HospitalPatient.create(patient=second_patient)
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create()

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        assert (
            'found deviations between opal.patients_hospitalpatient Django model'
            + ' and OpalDB.Patient_Hospital_Identifier legacy table!!!'
        ) in error
        assert (
            'The number of records in "opal.patients_hospitalpatient" '
            + 'and "OpalDB.Patient_Hospital_Identifier" tables does not match!'
        ) in error
        assert 'opal.patients_hospitalpatient: 2' in error
        assert 'OpalDB.Patient_Hospital_Identifier: 1' in error

    def test_hospital_patient_records_deviations(self) -> None:
        """Ensure the command detects the deviations in the "HospitalPatient" model and tables."""
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create()
        patient_factories.HospitalPatient.create(
            patient=patient_factories.Patient.create(legacy_id=1),
            site=hospital_settings_factories.Site.create(acronym='TST'),
        )

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        deviations_err = (
            'found deviations between opal.patients_hospitalpatient Django model'
            + ' and OpalDB.Patient_Hospital_Identifier legacy table!!!'
        )
        assert deviations_err in error
        assert 'opal.patients_hospitalpatient  <===>  OpalDB.Patient_Hospital_Identifier:' in error
        assert "(51, 'RVH', '9999996', 1)" in error
        assert "(1, 'TST', '9999996', 1)" in error

    def test_no_deviations_for_patients_with_users(self) -> None:
        """Ensure the command does not return an error if there are no deviations in "Patient" records."""
        self._create_two_fully_registered_patients()

        message, _error = self._call_command('find_deviations')
        assert patient_models.Patient.objects.count() == 2
        assert legacy_models.LegacyPatientControl.objects.count() == 2
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def test_no_deviations_for_patients_with_unregistered_users(self) -> None:
        """Ensure the command does not return deviations for unregistered "Patient" records."""
        self._create_two_fully_registered_patients()

        # Create unregistered Patient record
        patient_factories.Patient.create(
            legacy_id=None,
            ramq='RAMQ33333333',
            first_name='Third First Name',
            last_name='Third Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
        )
        # create unregistered SELF type caregiver
        patient_factories.CaregiverProfile.create(
            user=user_factories.Caregiver.create(
                email='opal@unregistered-example.com',
                language='en',
                phone_number='5149995555',
                first_name='Third First Name',
                last_name='Third Last Name',
                username='third_username',
            ),
            legacy_id=None,
        )

        message, _error = self._call_command('find_deviations')
        assert patient_models.Patient.objects.count() == 3
        assert legacy_models.LegacyPatientControl.objects.count() == 2
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def test_no_deviations_for_patients_without_user(self) -> None:
        """Ensure the command does not return deviations error for "Patient" records without users."""
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
            sex='Male',
            tel_num='5149995555',
            email='opal@example.com',
            language='en',
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=legacy_patient)
        # create legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(patient=legacy_patient)

        # create patient
        patient = patient_factories.Patient.create(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
        )
        # create hospital patient
        patient_factories.HospitalPatient.create(
            patient=patient,
            site=hospital_settings_factories.Site.create(acronym='RVH'),
        )

        # create another patient record

        # create a second legacy patient
        second_legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=98,
            ramq='RAMQ87654321',
            first_name='Second First Name',
            last_name='Second Last Name',
            date_of_birth=datetime(1950, 2, 3, tzinfo=timezone.get_current_timezone()),
            sex='Female',
            tel_num='5149991111',
            email='second.opal@example.com',
            language='fr',
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=second_legacy_patient)
        # create second legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(
            patient=second_legacy_patient,
            mrn='9999997',
            hospital=legacy_factories.LegacyHospitalIdentifierTypeFactory.create(code='MGH'),
        )

        # create second `Patient` record
        patient = patient_factories.Patient.create(
            legacy_id=98,
            ramq='RAMQ87654321',
            first_name='Second First Name',
            last_name='Second Last Name',
            date_of_birth=datetime(1950, 2, 3, tzinfo=timezone.get_current_timezone()),
            sex=patient_models.Patient.SexType.FEMALE,
        )
        # create second `HospitalPatient` record
        patient_factories.HospitalPatient.create(
            patient=patient,
            mrn='9999997',
            site=hospital_settings_factories.Site.create(acronym='MGH'),
        )

        message, _error = self._call_command('find_deviations')
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def test_patient_records_deviations_access_level(self) -> None:
        """Ensure the command returns an error if the access level does not match."""
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
            sex='Male',
            tel_num='5149995555',
            email='opal@example.com',
            language='en',
            access_level='1',
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=legacy_patient)
        user_factories.Caregiver.create(
            email='opal@example.com',
            language='en',
            phone_number='5149995555',
            first_name='First Name',
            last_name='Last Name',
        )
        # create patient
        patient = patient_factories.Patient.create(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
        )

        assert patient.data_access == patient_models.Patient.DataAccessType.ALL
        assert legacy_patient.access_level == '1'

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)
        assert 'The number of records in' not in error

        deviations_err = (
            'found deviations between opal.patients_patient Django model'
            + ' and OpalDB.Patient(UserType="Patient") legacy table!!!'
        )
        assert deviations_err in error

    def test_patient_records_deviations_date_of_death(self) -> None:
        """Ensure the command returns no error if the date of death matches."""
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
            sex='Male',
            tel_num='5149995555',
            email='opal@example.com',
            language='en',
            death_date=datetime(2024, 12, 31, tzinfo=timezone.get_current_timezone()),
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=legacy_patient)
        user_factories.Caregiver.create(
            email='opal@example.com',
            language='en',
            phone_number='5149995555',
            first_name='First Name',
            last_name='Last Name',
        )
        # create patient
        patient_factories.Patient.create(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
            date_of_death=datetime(2024, 12, 31, tzinfo=timezone.get_current_timezone()),
        )

        message, error = self._call_command('find_deviations')

        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message
        assert 'The number of records in' not in error

        deviations_err = (
            'found deviations between opal.patients_patient Django model'
            + ' and OpalDB.Patient(UserType="Patient") legacy table!!!'
        )
        # legacy datetimes are added as is whereas Django converts it to UTC
        # ensure the command can handle this
        assert deviations_err not in error

    def test_deviations_uneven_caregiver_records(self) -> None:
        """Ensure the command handles the cases when "User/Caregiver" model/tables have uneven number of records."""
        caregiver_user = user_factories.Caregiver.create(first_name='Homer', last_name='Simpson')
        patient_factories.CaregiverProfile.create(legacy_id=99, user=caregiver_user)
        legacy_factories.LegacyUserFactory.create(
            usersernum=99,
            usertypesernum=99,
            usertype=legacy_models.LegacyUserType.CAREGIVER,
        )
        legacy_factories.LegacyUserFactory.create(
            usersernum=100,
            usertypesernum=100,
            usertype=legacy_models.LegacyUserType.CAREGIVER,
        )
        legacy_factories.LegacyPatientFactory.create(patientsernum=99)
        legacy_factories.LegacyPatientFactory.create(patientsernum=100)

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        assert (
            'found deviations between opal.caregivers_caregiverprofile Django model'
            + ' and OpalDB.Patient(UserType="Caregiver") legacy table!!!'
        ) in error
        assert (
            'The number of records in "opal.caregivers_caregiverprofile"'
            + ' and "OpalDB.Patient(UserType="Caregiver")" tables does not match!'
        ) in error
        assert 'opal.caregivers_caregiverprofile: 1' in error
        assert 'OpalDB.Patient(UserType="Caregiver"): 2' in error

    def test_caregiver_records_deviations(self) -> None:
        """Ensure the command detects the deviations in the "User/Caregiver" records."""
        legacy_factories.LegacyUserFactory.create(
            usersernum=42,
            usertypesernum=51,
            usertype=legacy_models.LegacyUserType.CAREGIVER,
        )
        legacy_factories.LegacyPatientFactory.create(patientsernum=51, first_name='Homer', last_name='Simpson')
        user = user_factories.Caregiver.create(
            first_name='Homer',
            last_name='Simpson',
            email='test@test.com',
            username='test_username',
        )
        patient_factories.CaregiverProfile.create(legacy_id=42, user=user)

        with pytest.raises(CommandError) as exc:
            self._call_command('find_deviations')

        error = str(exc.value)

        assert (
            'found deviations between opal.caregivers_caregiverprofile Django model'
            + ' and OpalDB.Patient(UserType="Caregiver") legacy table!!!'
        ) in error

        assert 'opal.caregivers_caregiverprofile  <===>  OpalDB.Patient(UserType="Caregiver"):' in error
        assert "(42, 'Homer', 'Simpson', 'test@test.com', 'en', 'test_username')" in error
        assert ("(42, 'Homer', 'Simpson', 'test@test.com', 'en', 'username')") in error

    def test_no_caregiver_deviations(self) -> None:
        """Ensure the command does not return an error if there are no deviations in "Caregiver" records."""
        self._create_two_fully_registered_caregivers()

        message, _error = self._call_command('find_deviations')

        assert legacy_models.LegacyUsers.objects.count() == 2
        assert patient_models.CaregiverProfile.objects.count() == 2
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def test_no_caregiver_deviations_with_unregistered_users(self) -> None:
        """Ensure the command does not return deviations for unregistered "User/Caregiver" records."""
        self._create_two_fully_registered_caregivers()

        # Create unregistered "User/Caregiver" in Django DB
        caregiver_user = user_factories.Caregiver.create(
            email='opal@unregistered_example.com',
            language='en',
            phone_number='5149994444',
            first_name='Marge',
            last_name='Simpson',
            username='marge_username',
        )

        # create caregiver
        patient_factories.CaregiverProfile.create(
            legacy_id=None,
            user=caregiver_user,
        )

        message, _error = self._call_command('find_deviations')
        assert legacy_models.LegacyUsers.objects.count() == 2
        assert patient_models.CaregiverProfile.objects.count() == 3
        assert 'No deviations have been found in the "Patient and Caregiver" tables/models.' in message

    def _create_two_fully_registered_patients(self) -> None:
        """Create two fully registered patients in both legacy and Django databases."""
        # create legacy user
        legacy_factories.LegacyUserFactory.create(
            usersernum=99,
            usertypesernum=99,
            username='first_username',
        )
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
            sex='Male',
            tel_num='5149995555',
            email='opal@example.com',
            language='en',
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=legacy_patient)
        # create legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(patient=legacy_patient)

        # create patient
        patient = patient_factories.Patient.create(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
        )
        # create SELF type caregiver
        patient_factories.CaregiverProfile.create(
            user=user_factories.Caregiver.create(
                email='opal@example.com',
                language='en',
                phone_number='5149995555',
                first_name='First Name',
                last_name='Last Name',
                username='first_username',
            ),
            legacy_id=99,
        )
        # create hospital patient
        patient_factories.HospitalPatient.create(
            patient=patient,
            site=hospital_settings_factories.Site.create(acronym='RVH'),
        )

        # create another patient record

        # create a second legacy user
        legacy_factories.LegacyUserFactory.create(
            usersernum=98,
            usertypesernum=98,
            username='second_username',
        )

        # create a second legacy patient
        second_legacy_patient = legacy_factories.LegacyPatientFactory.create(
            patientsernum=98,
            ramq='RAMQ87654321',
            first_name='Second First Name',
            last_name='Second Last Name',
            date_of_birth=datetime(1950, 2, 3, tzinfo=timezone.get_current_timezone()),
            sex='Female',
            tel_num='5149991111',
            email='second.opal@example.com',
            language='fr',
        )
        legacy_factories.LegacyPatientControlFactory.create(patient=second_legacy_patient)
        # create second legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory.create(
            patient=second_legacy_patient,
            mrn='9999997',
            hospital=legacy_factories.LegacyHospitalIdentifierTypeFactory.create(code='MGH'),
        )

        # create second `Patient` record
        patient = patient_factories.Patient.create(
            legacy_id=98,
            ramq='RAMQ87654321',
            first_name='Second First Name',
            last_name='Second Last Name',
            date_of_birth=datetime(1950, 2, 3, tzinfo=timezone.get_current_timezone()),
            sex=patient_models.Patient.SexType.FEMALE,
        )

        # create second SELF type caregiver and second User record
        patient_factories.CaregiverProfile.create(
            legacy_id=98,
            user=user_factories.Caregiver.create(
                email='second.opal@example.com',
                phone_number='5149991111',
                language='fr',
                first_name='Second First Name',
                last_name='Second Last Name',
                username='second_username',
            ),
        )

        # create second `HospitalPatient` record
        patient_factories.HospitalPatient.create(
            patient=patient,
            mrn='9999997',
            site=hospital_settings_factories.Site.create(acronym='MGH'),
        )

    def _create_two_fully_registered_caregivers(self) -> None:
        """Create two fully registered caregivers in both legacy and Django databases."""
        # create legacy user
        legacy_factories.LegacyUserFactory.create(
            usersernum=99,
            usertypesernum=100,
            usertype=legacy_models.LegacyUserType.CAREGIVER,
            username='first_username',
        )
        # create legacy caregiver
        legacy_factories.LegacyPatientFactory.create(
            patientsernum=100,
            ramq='',
            first_name='Homer',
            last_name='Simpson',
            tel_num='5149995555',
            email='opal@example.com',
            language='en',
        )

        first_caregiver_user = user_factories.Caregiver.create(
            email='opal@example.com',
            language='en',
            phone_number='5149995555',
            first_name='Homer',
            last_name='Simpson',
            username='first_username',
        )

        # create caregiver
        patient_factories.CaregiverProfile.create(
            legacy_id=99,
            user=first_caregiver_user,
        )

        # create another caregiver record

        # create a second legacy user
        legacy_factories.LegacyUserFactory.create(
            usersernum=98,
            usertypesernum=97,
            usertype=legacy_models.LegacyUserType.CAREGIVER,
            username='second_username',
        )

        # create a second legacy caregiver
        legacy_factories.LegacyPatientFactory.create(
            patientsernum=97,
            ramq='RAMQ87654321',
            first_name='Bart',
            last_name='Simpson',
            date_of_birth=datetime(1950, 2, 3, tzinfo=timezone.get_current_timezone()),
            sex='Male',
            tel_num='5149991111',
            email='second.opal@example.com',
            language='fr',
        )

        # create second User record
        second_careguver_user = user_factories.Caregiver.create(
            email='second.opal@example.com',
            phone_number='5149991111',
            language='fr',
            first_name='Bart',
            last_name='Simpson',
            username='second_username',
        )

        # create second `Caregiver` record
        patient_factories.CaregiverProfile.create(
            legacy_id=98,
            user=second_careguver_user,
        )


class TestQuestionnaireRespondentsDeviationsCommand(CommandTestMixin):
    """Test class for the custom command that detects `Questionnaire respondents` sync deviations."""

    def test_deviations_no_respondents(self, django_db_blocker: DjangoDbBlocker) -> None:
        """Ensure the command does not fail if there are no questionnaires with respondents."""
        with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
            conn.execute('SET FOREIGN_KEY_CHECKS=0; DELETE FROM answerQuestionnaire;')
            conn.close()

        message, _error = self._call_command('find_questionnaire_respondent_deviations')
        assert 'No sync errors have been found in the in the questionnaire respondent data.' in message

    def test_questionnaire_respondents_deviations(
        self,
        questionnaire_data: None,
        django_db_blocker: DjangoDbBlocker,
    ) -> None:
        """Ensure the command detects the deviations between "answerQuestionnaire" table and `CaregiverProfile`."""
        with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
            query = """
                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT';

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID_1',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT test1'
                WHERE ID = 184;

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID_2',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT test2'
                WHERE ID = 189;

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT test3'
                WHERE ID = 190;

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = '',
                    `respondentDisplayName` = ''
                WHERE ID = 184;
            """
            conn.execute(query)
            conn.close()

        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT',
            username='firebase hashed user UID',
        )

        # this user should not be included to the error list
        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT test1',
            username='firebase hashed user UID_1',
        )

        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT test2_2',
            username='firebase hashed user UID_2',
        )

        with pytest.raises(CommandError) as exc:
            self._call_command('find_questionnaire_respondent_deviations')

        error = str(exc.value)
        assert 'found deviations in the questionnaire respondents!!!' in error
        assert "('', '')" in error
        assert "('firebase hashed user UID_2', 'TEST NAME RESPONDENT test2_2')" in error
        assert "('firebase hashed user UID', 'TEST NAME RESPONDENT test3')" in error
        assert "('firebase hashed user UID_2', 'TEST NAME RESPONDENT test2')" in error

    def test_no_questionnaire_respondents_deviations(self, django_db_blocker: DjangoDbBlocker) -> None:
        """Ensure the command does not return an error if no sync deviations for respondents' names."""
        with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
            query = """
                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT';

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID_1',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT test1'
                WHERE ID = 184;

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID_2',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT test2'
                WHERE ID = 189;

                UPDATE answerQuestionnaire
                SET
                    `respondentUsername` = 'firebase hashed user UID',
                    `respondentDisplayName` = 'TEST NAME RESPONDENT'
                WHERE ID = 190;
            """
            conn.execute(query)
            conn.close()

        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT',
            username='firebase hashed user UID',
        )

        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT test1',
            username='firebase hashed user UID_1',
        )

        user_factories.Caregiver.create(
            first_name='TEST NAME',
            last_name='RESPONDENT test2',
            username='firebase hashed user UID_2',
        )

        message, _error = self._call_command('find_questionnaire_respondent_deviations')
        assert 'No sync errors have been found in the in the questionnaire respondent data.' in message


class TestUpdateOrmsPatientsCommand(CommandTestMixin):
    """Test class for the custom command that updates patients' UUIDs in the ORMS."""

    def test_orms_patients_update_with_no_patients(self) -> None:
        """Ensure the command does not fail if there are no patient records."""
        message, _error = self._call_command('update_orms_patients')
        assert 'Updated 0 out of 0 patients.' in message

    def test_orms_patients_update_with_no_hospital_patients(self) -> None:
        """Ensure the command does not fail if there are no hospital patient records (e.g., MRN/site)."""
        # Create patients
        patient_factories.Patient.create(id=1, ramq='RAMQ11111111')
        patient_factories.Patient.create(id=2, ramq='RAMQ22222222')
        patient_factories.Patient.create(id=3, ramq='RAMQ33333333')
        message, _error = self._call_command('update_orms_patients')
        assert 'Updated 0 out of 3 patients.' in message

    @pytest.mark.usefixtures('set_orms_disabled')
    def test_orms_patients_update_orms_disabled(self) -> None:
        """Ensure the command does not fail if ORMS is disabled."""
        message, error = self._call_command('update_orms_patients')
        assert 'ORMS System not enabled, exiting command' in message
        assert not error

    def test_orms_patients_update_with_request_exception(self, mocker: MockerFixture) -> None:
        """Ensure the command handles exceptions during POST requests to the ORMS."""
        # Create test data
        site = patient_factories.Site.create(acronym='RVH')
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
            mrn='9999999',
        )
        # Create mock POST request
        mock_post = RequestMockerTest.mock_requests_post(mocker, {})
        mock_post.side_effect = requests.RequestException('request failed')
        mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
        # Call the command
        _message, error = self._call_command('update_orms_patients')

        number_of_patients = patient_models.Patient.objects.all().count()
        assert error.count("An error occurred during patient's UUID update!") == number_of_patients

    def test_orms_patients_update_unsuccessful_response(self, mocker: MockerFixture) -> None:
        """Ensure the command handles unsuccessful responses during POST requests to the ORMS."""
        # Create test data
        site = patient_factories.Site.create(acronym='RVH')
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
            mrn='9999999',
        )
        # Create mock POST request
        mock_post = RequestMockerTest.mock_requests_post(mocker, {})
        mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
        # Call the command
        message, error = self._call_command('update_orms_patients')

        assert "An error occurred during patients' UUID update!" not in error
        assert 'Updated 0 out of' in message
        assert 'The following patients were not updated:' in error

    def test_orms_patients_successful_update(self, mocker: MockerFixture) -> None:
        """Ensure the command does not have any errors during successful ORMS patients update."""
        # Create test data
        site = patient_factories.Site.create(acronym='RVH')
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient.create(
            site=site,
            patient=patient_factories.Patient.create(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
            mrn='9999999',
        )
        # Create mock POST request
        mock_post = RequestMockerTest.mock_requests_post(mocker, {})
        mock_post.return_value.status_code = HTTPStatus.OK
        # Call the command
        message, error = self._call_command('update_orms_patients')

        patients_num = patient_models.Patient.objects.all().count()
        assert "An error occurred during patients' UUID update!" not in error
        assert f'Updated {patients_num} out of {patients_num}' in message
        assert 'The following patients were not updated:' not in error


class TestMigrateUsersCommand(CommandTestMixin):
    """Tests for the migrate_users command."""

    def test_migrate_users_admins_legacyoauser_pass(self) -> None:
        """Test import pass for multiple `Administrators` Legacy OAUsers."""
        module = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        admingroup = user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        role = legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')

        legacy_factories.LegacyOAUserFactory.create(oa_role=role)
        legacy_factories.LegacyOAUserFactory.create(oa_role=role)

        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=role, module=module)
        message, _error = self._call_command('migrate_users')

        assert 'Migrated 2 of 2 users (2 system administrators and 0 registrants)' in message
        assert ClinicalStaff.objects.all().count() == 2
        clincal_staff_user = ClinicalStaff.objects.all()[0]
        assert clincal_staff_user.is_staff
        assert clincal_staff_user.is_superuser
        assert clincal_staff_user.groups.get() == admingroup

    def test_migrate_users_registrants_legacyoauser_pass(self) -> None:
        """Test import pass for multiple `Registrants` Legacy OAUsers."""
        module = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        # Creating needed groups
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        registrant_group = user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')
        role = legacy_factories.LegacyOARoleFactory.create(name_en='AnyRole')

        legacy_factories.LegacyOAUserFactory.create(oa_role=role)
        legacy_factories.LegacyOAUserFactory.create(oa_role=role)

        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=role, module=module, access=3)
        message, _error = self._call_command('migrate_users')

        assert 'Migrated 2 of 2 users (0 system administrators and 2 registrants)' in message
        assert ClinicalStaff.objects.all().count() == 2
        clincal_staff_user = ClinicalStaff.objects.all()[0]
        assert clincal_staff_user.groups.get() == registrant_group

    def test_migrate_users_nonadmins_legacyoauser_pass(self) -> None:
        """Test import pass for multiple non-admins and no write access on `Patient` module, from Legacy OAUsers."""
        module = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        # Creating needed groups
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')
        role = legacy_factories.LegacyOARoleFactory.create(name_en='AnyRole')

        legacy_factories.LegacyOAUserFactory.create(oa_role=role)
        legacy_factories.LegacyOAUserFactory.create(oa_role=role)

        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=role, module=module)
        message, _error = self._call_command('migrate_users')

        assert 'Migrated 2 of 2 users (0 system administrators and 0 registrants)' in message
        assert ClinicalStaff.objects.all().count() == 2

    def test_migrate_users_duplicate_legacyoauser_fail(self) -> None:
        """Test import fail for re-entering same OAUser of type Administration."""
        module = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        role = legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')

        user = legacy_factories.LegacyOAUserFactory.create(oa_role=role)

        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=role, module=module)
        message, error = self._call_command('migrate_users')

        assert 'Migrated 1 of 1 users (1 system administrators and 0 registrants)' in message
        assert ClinicalStaff.objects.all().count() == 1

        message, error = self._call_command('migrate_users')
        errormsg = (
            "Error: {'username': ['A user with that username already exists.']}"
            + f' when saving username: {user.username}\n'
        )
        assert errormsg in error
        assert 'Migrated 0 of 1 users (0 system administrators and 0 registrants)' in message

    def test_migrate_users_alltypes_legacyoauser_pass(self) -> None:
        """Test import pass for mixed type of users from Legacy OAUsers."""
        patientmodule = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        anymodule = legacy_factories.LegacyModuleFactory.create(name_en='AnyModule')
        # Creating needed groups
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        adminrole = legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')
        nonadminrole_patient = legacy_factories.LegacyOARoleFactory.create(name_en='PatientRole')
        nonadminrole_nonpatient = legacy_factories.LegacyOARoleFactory.create(name_en='AnyRole')

        # administrators
        legacy_factories.LegacyOAUserFactory.create(oa_role=adminrole)
        legacy_factories.LegacyOAUserFactory.create(oa_role=adminrole)
        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=adminrole, module=anymodule)
        # registrants
        legacy_factories.LegacyOAUserFactory.create(oa_role=nonadminrole_patient)
        legacy_factories.LegacyOAUserFactory.create(oa_role=nonadminrole_patient)
        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=nonadminrole_patient, module=patientmodule, access=3)
        # other users
        legacy_factories.LegacyOAUserFactory.create(oa_role=nonadminrole_nonpatient)
        legacy_factories.LegacyOAUserFactory.create(oa_role=nonadminrole_nonpatient)
        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=nonadminrole_nonpatient, module=anymodule)

        message, _error = self._call_command('migrate_users')

        assert 'Migrated 6 of 6 users (2 system administrators and 2 registrants)' in message
        assert ClinicalStaff.objects.all().count() == 6

    def test_migrate_users_duplicate_registrants_legacyoauser_fail(self) -> None:
        """Test import fail for re-entering same OAUser of type registrant."""
        module = legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')
        role = legacy_factories.LegacyOARoleFactory.create(name_en='AnyRole')
        user = legacy_factories.LegacyOAUserFactory.create(oa_role=role)
        legacy_factories.LegacyOARoleModuleFactory.create(oa_role=role, module=module, access=3)

        # Creating needed groups
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        message, error = self._call_command('migrate_users')

        assert 'Migrated 1 of 1 users (0 system administrators and 1 registrants' in message
        assert ClinicalStaff.objects.all().count() == 1

        message, error = self._call_command('migrate_users')

        errormsg = (
            "Error: {'username': ['A user with that username already exists.']}"
            + f' when saving username: {user.username}\n'
        )
        assert errormsg in error

    def test_deleted_user_not_migrated(self) -> None:
        """Ensure that deleted users are not migrated."""
        legacy_factories.LegacyModuleFactory.create(name_en='Patients')
        user_factories.GroupFactory.create(name=settings.ADMIN_GROUP_NAME)
        user_factories.GroupFactory.create(name=settings.REGISTRANTS_GROUP_NAME)
        legacy_factories.LegacyOARoleFactory.create(name_en='System Administrator')
        role = legacy_factories.LegacyOARoleFactory.create(name_en='AnyRole')

        deleted_user = legacy_factories.LegacyOAUserFactory.create(oa_role=role, is_deleted=True)
        actual_user = legacy_factories.LegacyOAUserFactory.create(oa_role=role)

        message, _error = self._call_command('migrate_users')

        assert 'Migrated 1 of 1 users (0 system administrators and 0 registrants)' in message
        assert ClinicalStaff.objects.count() == 1
        assert ClinicalStaff.objects.filter(username=actual_user.username).exists()
        assert not ClinicalStaff.objects.filter(username=deleted_user.username).exists()


class TestMigrateLegacyUsageStatisticsMigration(CommandTestMixin):
    """Test class for legacy usage statistics data migrations from legacy DB."""

    def test_migrate_legacy_usage_statistics_with_no_legacy_statistics(self) -> None:
        """Test import success but no legacy statistics exist."""
        message, _error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_empty_file.csv',
            'opal/tests/fixtures/test_empty_file.csv',
        )

        assert 'Number of imported legacy activity log is: 0' in message
        assert 'Number of imported legacy data received log is: 0' in message
        assert DailyUserAppActivity.objects.all().count() == 0
        assert DailyUserPatientActivity.objects.all().count() == 0
        assert DailyPatientDataReceived.objects.all().count() == 0

    def test_migrate_legacy_usage_statistics_with_success(self) -> None:
        """Ensure the command handle the legacy usage statistics migration with success."""
        self._create_test_self_registered_patient(99)

        message, _error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log.csv',
            'opal/tests/fixtures/test_data_received_log.csv',
        )

        assert 'Number of imported legacy activity log is: 1' in message
        assert 'Number of imported legacy data received log is: 1' in message
        assert DailyUserAppActivity.objects.all().count() == 1
        assert DailyUserPatientActivity.objects.all().count() == 1
        assert DailyPatientDataReceived.objects.all().count() == 1

    def test_migrate_legacy_usage_statistics_with_success_no_date_value(self) -> None:
        """Ensure the command handle the legacy usage statistics migration using no date test data."""
        self._create_test_self_registered_patient(99)

        message, _error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log.csv',
            'opal/tests/fixtures/test_data_received_log_no_date.csv',
        )

        assert 'Number of imported legacy activity log is: 1' in message
        assert 'Number of imported legacy data received log is: 1' in message
        assert DailyUserAppActivity.objects.all().count() == 1
        assert DailyUserPatientActivity.objects.all().count() == 1
        assert DailyPatientDataReceived.objects.all().count() == 1

    def test_migrate_legacy_patient_activity_logs_with_failed(self) -> None:
        """Test the legacy patient activity log migration failed due to unexisting patient."""
        self._create_test_self_registered_patient(100)

        message, error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log.csv',
            'opal/tests/fixtures/test_data_received_log.csv',
        )

        assert 'Cannot prepare `DailyUserPatientActivity` instance for patient (legacy ID: 99),' in error
        assert 'Cannot prepare `DailyUserAppActivity` instance for patient (legacy ID: 99),' in error
        assert 'Patient (legacy ID: 99) does not exist in system.' in error
        assert 'Number of imported legacy activity log is: 0' in message
        assert 'Cannot prepare `DailyPatientDataReceived` instance for patient (legacy ID: 99),' in error
        assert 'Number of imported legacy data received log is: 0' in message
        assert DailyUserAppActivity.objects.all().count() == 0
        assert DailyUserPatientActivity.objects.all().count() == 0
        assert DailyPatientDataReceived.objects.all().count() == 0

    def test_migrate_legacy_usage_statistics_with_success_with_large_data(self) -> None:
        """Ensure the command handle the legacy usage statistics migration using large test data."""
        self._create_test_self_registered_patient(99)

        message, _error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log_large_data.csv',
            'opal/tests/fixtures/test_data_received_log_large_data.csv',
            '--batch-size=10',
        )

        assert 'Number of imported legacy activity log is: 1000' in message
        assert 'Number of imported legacy data received log is: 1000' in message
        assert DailyUserAppActivity.objects.all().count() == 1000
        assert DailyUserPatientActivity.objects.all().count() == 1000
        assert DailyPatientDataReceived.objects.all().count() == 1000

    def test_migrate_legacy_usage_statistics_skip_exist_data(self) -> None:
        """Ensure the command handle the legacy usage statistics migration using existed data."""
        self._create_test_self_registered_patient(99)

        self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log.csv',
            'opal/tests/fixtures/test_data_received_log.csv',
        )
        message, _error = self._call_command(
            'migrate_legacy_usage_statistics',
            'opal/tests/fixtures/test_activity_log.csv',
            'opal/tests/fixtures/test_data_received_log.csv',
        )

        assert 'Number of imported legacy activity log is: 0' in message
        assert 'Number of imported legacy data received log is: 0' in message
        assert DailyUserAppActivity.objects.all().count() == 1
        assert DailyUserPatientActivity.objects.all().count() == 1
        assert DailyPatientDataReceived.objects.all().count() == 1

    def _create_test_self_registered_patient(self, patient_id: int) -> None:
        """
        Create a test self registered patient.

        Args:
            patient_id: legacy id of patient instance
        """
        patient = patient_factories.Patient.create(
            legacy_id=patient_id,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone()),
        )
        caregiver = caregiver_factories.CaregiverProfile.create(
            user=user_factories.Caregiver.create(
                language='en',
                phone_number='5149999999',
                first_name='First Name',
                last_name='Last Name',
                username='first_username',
            ),
            legacy_id=patient_id,
        )
        relationship_type = patient_factories.RelationshipType.create(name='Self')
        patient_factories.Relationship.create(
            patient=patient,
            caregiver=caregiver,
            type=relationship_type,
        )
