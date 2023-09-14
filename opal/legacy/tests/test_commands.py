import uuid
from datetime import date, datetime
from http import HTTPStatus

from django.db import connections
from django.utils import timezone

import pytest
import requests
from pytest_django.plugin import _DatabaseBlocker  # noqa: WPS450
from pytest_mock.plugin import MockerFixture

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import SecurityAnswer, SecurityQuestion
from opal.core.test_utils import CommandTestMixin, RequestMockerTest
from opal.hospital_settings import factories as hospital_settings_factories
from opal.legacy import factories as legacy_factories
from opal.patients import factories as patient_factories
from opal.patients.models import Patient, RelationshipStatus, RelationshipType
from opal.users import factories as user_factories

from ..management.commands import migrate_caregivers

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestSecurityQuestionsMigration(CommandTestMixin):
    """Test class for security questions migration."""

    def test_import_fails_question_exists(self) -> None:
        """Test import fails due to security question already exists."""
        legacy_factories.LegacySecurityQuestionFactory()
        caregiver_factories.SecurityQuestion(title_en='What is the name of your first pet?')
        message, error = self._call_command('migrate_securityquestions')
        question = SecurityQuestion.objects.all()
        assert len(question) != 2
        assert message == (
            'Security question sernum: 1, title: What is the name of your first pet? exists already, skipping\n'
        )
        assert error == ''

    def test_import_succeeds(self) -> None:
        """Test import a security question successfully."""
        legacy_factories.LegacySecurityQuestionFactory()
        message, error = self._call_command('migrate_securityquestions')
        question = SecurityQuestion.objects.all()
        assert len(question) == 1
        assert question[0].title_en == 'What is the name of your first pet?'  # type: ignore[attr-defined]
        assert question[0].title_fr == 'Quel est le nom de votre premier animal de compagnie?'  # type: ignore[attr-defined]  # noqa: E501
        assert message == (
            'Imported security question, sernum: 1, title: What is the name of your first pet?\n'
        )
        assert error == ''


class TestSecurityAnswersMigration(CommandTestMixin):
    """Test class for security answers migration."""

    def test_import_fails_legacy_user_not_exists(self) -> None:
        """Test import fails due to legacy user not exists."""
        patientsernum = 99
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert not answer
        assert message == ''
        assert error == (
            'Legacy user does not exist, usertypesernum: 99\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_multiple_legacy_user(self) -> None:
        """Test import fails due to multiple legacy users."""
        patientsernum = 99
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert not answer
        assert message == ''
        assert error == (
            'Found more than one related legacy users, usertypesernum: 99\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_user_not_exists(self) -> None:
        """Test import fails due to user not exists."""
        patientsernum = 99
        username = 'no_name'
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum, username=username)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert not answer
        assert message == ''
        assert error == (
            'User does not exist, username: no_name\n'
            + 'Security answer import failed, sernum: 1, details: User does not exist\n'
        )

    def test_import_fails_no_caregiver_profile(self) -> None:
        """Test import fails due to caregiver profile not exists."""
        patientsernum = 99
        username = 'no_name'
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum, username=username)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)
        user_factories.User(username=username)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert not answer
        assert message == ''
        assert error == (
            'Security answer import failed, sernum: 1, details: Caregiver does not exist\n'
        )

    def test_import_fails_security_answer_exists(self) -> None:
        """Test import fails due to security answer already exists."""
        patientsernum = 99
        username = 'no_name'
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum, username=username)
        legacy_answer = legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)
        user = user_factories.User(username=username)
        caregiver = caregiver_factories.CaregiverProfile(user=user)
        caregiver_factories.SecurityAnswer(
            user=caregiver,
            question=legacy_answer.securityquestionsernum.questiontext_en,
            answer=legacy_answer.answertext,
        )

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert len(answer) != 2
        assert message == 'Security answer already exists, sernum: 1\n'
        assert error == ''

    def test_import_succeeds(self) -> None:
        """Test import succeeds."""
        patientsernum = 99
        username = 'no_name'
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum, username=username)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)
        user = user_factories.User(username=username, language='en')
        caregiver_factories.CaregiverProfile(user=user)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert len(answer) == 1
        assert answer[0].question == 'What is the name of your first pet?'
        assert answer[0].answer == 'bird'
        assert message == 'Security answer import succeeded, sernum: 1\n'
        assert error == ''

    def test_import_question_fr_by_user_language(self) -> None:
        """Test import question language by user language."""
        patientsernum = 99
        username = 'no_name'
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=patientsernum)
        legacy_factories.LegacyUserFactory(usertypesernum=patientsernum, username=username)
        legacy_factories.LegacySecurityAnswerFactory(patientsernum=legacy_patient)
        user = user_factories.User(username=username, language='fr')
        caregiver_factories.CaregiverProfile(user=user)

        message, error = self._call_command('migrate_securityanswers')
        answer = SecurityAnswer.objects.all()
        assert len(answer) == 1
        assert answer[0].question == 'Quel est le nom de votre premier animal de compagnie?'
        assert answer[0].answer == 'bird'
        assert message == 'Security answer import succeeded, sernum: 1\n'
        assert error == ''


class TestPatientAndPatientIdentifierMigration(CommandTestMixin):
    """Test class for security answers migration."""

    def test_import_patient(self) -> None:
        """The patient is imported with the correct data."""
        legacy_patient = legacy_factories.LegacyPatientFactory()

        message, error = self._call_command('migrate_patients')

        assert 'Imported patient, legacy_id: 51\n' in message
        patient = Patient.objects.get(legacy_id=51)

        assert patient.date_of_birth == date(2018, 1, 1)
        assert patient.sex == Patient.SexType.MALE
        assert patient.first_name == legacy_patient.firstname
        assert patient.last_name == legacy_patient.lastname
        assert patient.ramq == legacy_patient.ssn

    @pytest.mark.parametrize(('data_access', 'legacy_data_access'), [
        (Patient.DataAccessType.ALL, '3'),
        (Patient.DataAccessType.NEED_TO_KNOW, '1'),
    ])
    def test_import_patient_data_access(self, data_access: Patient.DataAccessType, legacy_data_access: str) -> None:
        """The patient is imported with the data access level."""
        legacy_factories.LegacyPatientFactory(accesslevel=legacy_data_access)

        message, error = self._call_command('migrate_patients')

        assert 'Imported patient, legacy_id: 51\n' in message
        patient = Patient.objects.get(legacy_id=51)
        assert patient.data_access == data_access

    def test_import_legacy_patient_not_exist_fail(self) -> None:
        """Test import fails no legacy patient exists."""
        legacy_patient = ''
        message, error = self._call_command('migrate_patients')
        assert not legacy_patient
        assert error.strip() == (
            'No legacy patients exist'
        )

    def test_import_legacy_patient_already_exist_fail(self) -> None:
        """Test import fails patient already exists."""
        legacy_factories.LegacyPatientFactory(patientsernum=51)
        patient_factories.Patient(legacy_id=51)
        message, error = self._call_command('migrate_patients')
        assert 'Patient with legacy_id: 51 already exists, skipping\n' in message

    def test_import_patient_pass_no_identifier_exists(self) -> None:
        """Test import pass for patient fail for patient identifier."""
        legacy_factories.LegacyPatientFactory()
        message, error = self._call_command('migrate_patients')
        assert 'No hospital patient identifiers for patient with legacy_id: 51 exist, skipping\n' in message

    def test_import_patient_patientidentifier_pass(self) -> None:
        """Test import pass for patient and patient identifier."""
        legacy_factories.LegacyPatientFactory()
        legacy_factories.LegacyPatientHospitalIdentifierFactory()
        patient_factories.Patient()
        hospital_settings_factories.Site(code='RVH')

        message, error = self._call_command('migrate_patients')
        assert 'Imported patient, legacy_id: 51\n' in message
        assert 'Imported patient_identifier, legacy_id: 51, mrn: 9999996\n' in message
        assert 'Number of imported patients is: 1\n' in message

    def test_import_pass_patientidentifier_only(self) -> None:
        """Test import fail for patient and pass patient identifier."""
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=10)
        patient_factories.Patient(legacy_id=10)
        legacy_factories.LegacyPatientHospitalIdentifierFactory(patientsernum=legacy_patient)
        hospital_settings_factories.Site(code='RVH')

        message, error = self._call_command('migrate_patients')
        assert 'Patient with legacy_id: 10 already exists, skipping\n' in message
        assert 'Imported patient_identifier, legacy_id: 10, mrn: 9999996\n' in message
        assert 'Number of imported patients is: 0\n' in message

    def test_import_pass_patient_only(self) -> None:
        """Test import pass for patient and fail patient identifier already exists."""
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=99)
        patient = patient_factories.Patient(legacy_id=99)
        code = legacy_factories.LegacyHospitalIdentifierTypeFactory(code='TEST')
        legacy_factories.LegacyPatientHospitalIdentifierFactory(
            hospitalidentifiertypecode=code,
            patientsernum=legacy_patient,
            mrn='9999996',
        )
        site = hospital_settings_factories.Site(code='TEST')
        patient_factories.HospitalPatient(
            site=site,
            patient=patient,
            mrn='9999996',
        )

        message, error = self._call_command('migrate_patients')
        assert 'Patient with legacy_id: 99 already exists, skipping\n' in message
        assert 'Patient identifier legacy_id: 99, mrn:9999996 already exists, skipping\n' in message
        assert 'Number of imported patients is: 0\n' in message

    def test_import_failure_multiple_mrns_at_same_site(self) -> None:
        """Test import fail for patient with multiple MRNs at the same site."""
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=10)
        patient_factories.Patient(legacy_id=10)
        code = legacy_factories.LegacyHospitalIdentifierTypeFactory(code='TEST')
        legacy_factories.LegacyPatientHospitalIdentifierFactory(
            hospitalidentifiertypecode=code,
            patientsernum=legacy_patient,
            mrn='9999996',
        )
        legacy_factories.LegacyPatientHospitalIdentifierFactory(
            hospitalidentifiertypecode=code,
            patientsernum=legacy_patient,
            mrn='9999997',
        )
        hospital_settings_factories.Site(code='TEST')

        message, error = self._call_command('migrate_patients')

        assert 'Patient with legacy_id: 10 already exists, skipping\n' in message
        assert 'Imported patient_identifier, legacy_id: 10, mrn: 9999996\n' in message
        assert 'Number of imported patients is: 0\n' in message
        assert error == (
            'Cannot import patient hospital identifier for patient (ID: 10, MRN: 9999997),'
            + ' already has an MRN at the same site (TEST)\n'
        )


class TestUsersCaregiversMigration(CommandTestMixin):
    """Test class for users and caregivers migrations from legacy DB."""

    def test_import_user_caregiver_no_legacy_users(self) -> None:
        """Test import fails no legacy users exist."""
        message, error = self._call_command('migrate_caregivers')

        assert 'Number of imported caregivers is: 0' in message

    def test_import_user_caregiver_no_patient_exist(self) -> None:
        """Test import fails, a corresponding patient in new backend does not exist."""
        legacy_factories.LegacyUserFactory(usertypesernum=99)

        message, error = self._call_command('migrate_caregivers')

        assert 'Patient with sernum: 99, does not exist, skipping.\n' in error

    def test_import_user_caregiver_already_exist(self) -> None:
        """Test import fails, caregiver profile has already been migrated."""
        legacy_user = legacy_factories.LegacyUserFactory(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient(legacy_id=99)
        patient_factories.CaregiverProfile(
            legacy_id=legacy_user.usersernum,
            # use same name to satisfy self relationship constraint
            user__first_name=patient.first_name,
            user__last_name=patient.last_name,
        )

        message, error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0\n' in message

    def test_import_user_caregiver_exists_relation(self) -> None:
        """Test import relation fails, relation already exists."""
        legacy_factories.LegacyUserFactory(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient(legacy_id=99)
        relationship_type = RelationshipType.objects.self_type()
        caregiver = patient_factories.CaregiverProfile(legacy_id=55)
        patient_factories.Relationship(
            patient=patient,
            caregiver=caregiver,
            type=relationship_type,
            status=RelationshipStatus.CONFIRMED,
        )

        message, error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0\n' in message
        assert 'Self relationship for patient with legacy_id: 99 already exists.\n' in message

    def test_import_user_caregiver_no_relation(self) -> None:
        """Test import pass for relationship for already migrated caregiver."""
        legacy_user = legacy_factories.LegacyUserFactory(usersernum=55, usertypesernum=99)
        patient = patient_factories.Patient(legacy_id=99)
        patient_factories.CaregiverProfile(
            legacy_id=legacy_user.usersernum,
            # use same name to satisfy self relationship constraint
            user__first_name=patient.first_name,
            user__last_name=patient.last_name,
        )

        message, error = self._call_command('migrate_caregivers')

        assert 'Nothing to be done for sernum: 55, skipping.\n' in message
        assert 'Number of imported caregivers is: 0\n' in message
        assert 'Self relationship for patient with legacy_id: 99 has been created.\n' in message

    def test_import_new_user_caregiver_no_relation(self) -> None:
        """Test import pass for caregiver profile and relationship."""
        legacy_patient = legacy_factories.LegacyPatientFactory(patientsernum=99)
        legacy_factories.LegacyUserFactory(usersernum=55, usertypesernum=99)
        patient_factories.Patient(
            legacy_id=99,
            first_name=legacy_patient.firstname,
            last_name=legacy_patient.lastname,
        )
        message, error = self._call_command('migrate_caregivers')

        assert 'Legacy caregiver with sernum: 55 has been migrated\n' in message
        assert 'Number of imported caregivers is: 1\n' in message
        assert 'Self relationship for patient with legacy_id: 99 has been created.\n' in message

    def test_import_new_user_caregiver_with_relation(self) -> None:
        """Test import pass for multiple caregiver profiles and their relations."""
        legacy_patient1 = legacy_factories.LegacyPatientFactory(patientsernum=99)
        legacy_patient2 = legacy_factories.LegacyPatientFactory(patientsernum=100)
        legacy_factories.LegacyUserFactory(usersernum=55, usertypesernum=99, usertype='Patient', username='test1')
        legacy_factories.LegacyUserFactory(usersernum=56, usertypesernum=100, usertype='Patient', username='test2')
        patient_factories.Patient(
            legacy_id=99,
            first_name=legacy_patient1.firstname,
            last_name=legacy_patient1.lastname,
            ramq='RAMQ12345678',
        )
        patient_factories.Patient(
            legacy_id=100,
            first_name=legacy_patient2.firstname,
            last_name=legacy_patient2.lastname,
        )
        message, error = self._call_command('migrate_caregivers')

        assert 'Legacy caregiver with sernum: 55 has been migrated\n' in message
        assert 'Legacy caregiver with sernum: 56 has been migrated\n' in message
        assert 'Self relationship for patient with legacy_id: 99 has been created.\n' in message
        assert 'Self relationship for patient with legacy_id: 100 has been created.\n' in message
        assert 'Number of imported caregivers is: 2\n' in message

    def test_import_new_user_phone_number_converted(self) -> None:
        """Ensure that the phone number is correctly converted to a string and prefixed with the country code."""
        legacy_patient = legacy_factories.LegacyPatientFactory(telnum=514123456789)
        legacy_user = legacy_factories.LegacyUserFactory()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert profile.user.phone_number == '+1514123456789'

    def test_import_new_user_phone_number_missing(self) -> None:
        """Ensure that a legacy patient without a phone number is correctly migrated."""
        legacy_patient = legacy_factories.LegacyPatientFactory(telnum=None)
        legacy_user = legacy_factories.LegacyUserFactory()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert profile.user.phone_number == ''

    def test_import_user_caregiver_has_unusable_password(self) -> None:
        """Ensure that migrated caregivers are assigned unusable passwords (since passwords aren't currently saved)."""
        legacy_patient = legacy_factories.LegacyPatientFactory()
        legacy_user = legacy_factories.LegacyUserFactory()

        command = migrate_caregivers.Command()
        profile = command._create_caregiver_and_profile(legacy_patient, legacy_user)

        assert not profile.user.has_usable_password()


class TestPatientsDeviationsCommand(CommandTestMixin):
    """Test class for the custom command that detects `Patient` model/tables deviations."""

    def test_deviations_no_patients(self) -> None:
        """Ensure the command does not fail if there are no patient records."""
        message, error = self._call_command('find_patients_deviations')
        assert 'No deviations have been found in the "Patient" tables/models.' in message

    def test_deviations_uneven_patient_records(self) -> None:
        """Ensure the command handles the cases when "Patient" model/tables have uneven number of records."""
        patient_factories.Patient(legacy_id=99, first_name='Test_1', ramq='RAMQ12345678')
        legacy_factories.LegacyPatientFactory(patientsernum=99)
        legacy_factories.LegacyPatientFactory(patientsernum=100)
        message, error = self._call_command('find_patients_deviations')
        assert 'found deviations in the "Patient" tables/models!!!' in error
        assert 'The number of records in "opal.patients_patient" and "OpalDB.Patient" tables does not match!' in error
        assert '"opal.patients_patient": 1' in error
        assert '"OpalDB.Patient": 2' in error

    def test_patient_records_deviations(self) -> None:
        """Ensure the command detects the deviations in the "Patient" model and tables."""
        legacy_factories.LegacyPatientFactory()
        patient_factories.Patient(legacy_id=1)
        message, error = self._call_command('find_patients_deviations')

        assert '{0}\n\n{1}'.format(
            'found deviations in the "Patient" tables/models!!!',
            120 * '-',
        ) in error

        assert 'OpalDB.Patient  <===>  opal.patients_patient:' in error
        assert "(1, '', 'Marge', 'Simpson', '1999-01-01', 'M', None, None, None, 'ALL')" in error
        assert (
            "(51, '123456', 'Marge', 'Simpson', '2018-01-01', 'M', '5149995555', 'test@test.com', 'en', 'ALL')"
        ) in error
        assert '{0}\n\n\n'.format(120 * '-')

    def test_deviations_uneven_hospi_patient_records(self) -> None:
        """Ensure the command handles the cases when "HospitalPatient" model/tables have uneven number of records."""
        patient_factories.HospitalPatient()
        patient_factories.HospitalPatient()
        legacy_factories.LegacyPatientHospitalIdentifierFactory()
        message, error = self._call_command('find_patients_deviations')
        assert 'found deviations in the "Patient" tables/models!!!' in error
        assert '{0}{1}'.format(
            'The number of records in "opal.patients_hospitalpatient" ',
            'and "OpalDB.Patient_Hospital_Identifier" tables does not match!',
        ) in error
        assert 'opal.patients_hospitalpatient: 2' in error
        assert 'OpalDB.Patient_Hospital_Identifier: 1' in error

    def test_hospital_patient_records_deviations(self) -> None:
        """Ensure the command detects the deviations in the "HospitalPatient" model and tables."""
        legacy_factories.LegacyPatientHospitalIdentifierFactory()
        patient_factories.HospitalPatient(
            patient=patient_factories.Patient(legacy_id=1),
            site=hospital_settings_factories.Site(code='TST'),
        )

        message, error = self._call_command('find_patients_deviations')
        assert 'found deviations in the "Patient" tables/models!!!' in error
        assert 'OpalDB.Patient_Hospital_Identifier  <===>  opal.patients_hospitalpatient:' in error
        assert "(51, 'RVH', '9999996', 1)" in error
        assert "(1, 'TST', '9999996', 1)" in error

    def test_no_patient_records_deviations(self) -> None:
        """Ensure the command does not return an error if there are no deviations in "Patient" records."""
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory(
            patientsernum=99,
            ssn='RAMQ12345678',
            firstname='First Name',
            lastname='Last Name',
            dateofbirth=timezone.make_aware(datetime(2018, 1, 1)),
            sex='Male',
            telnum='5149995555',
            email='opal@example.com',
            language='en',
        )
        # create legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory(patientsernum=legacy_patient)
        caregiver_factories.CaregiverProfile(
            user=user_factories.Caregiver(
                email='opal@example.com',
                language='en',
                phone_number='5149995555',
            ),
            legacy_id=99,
        )
        # create patient
        patient = patient_factories.Patient(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )
        # create hospital patient
        patient_factories.HospitalPatient(
            patient=patient,
            site=hospital_settings_factories.Site(code='RVH'),
        )

        # create another patient record

        # create a second legacy patient
        second_legacy_patient = legacy_factories.LegacyPatientFactory(
            patientsernum=98,
            ssn='RAMQ87654321',
            firstname='Second First Name',
            lastname='Second Last Name',
            dateofbirth=timezone.make_aware(datetime(1950, 2, 3)),
            sex='Female',
            telnum='5149991111',
            email='second.opal@example.com',
            language='fr',
        )
        # create second legacy HospitalPatient identifier
        legacy_factories.LegacyPatientHospitalIdentifierFactory(
            patientsernum=second_legacy_patient,
            mrn='9999997',
            hospitalidentifiertypecode=legacy_factories.LegacyHospitalIdentifierTypeFactory(code='MGH'),
        )

        # create second CaregiverProfile record
        caregiver_factories.CaregiverProfile(
            user=user_factories.Caregiver(
                email='second.opal@example.com',
                phone_number='5149991111',
                language='fr',
            ),
            legacy_id=98,
        )

        # create second `Patient` record
        patient = patient_factories.Patient(
            legacy_id=98,
            ramq='RAMQ87654321',
            first_name='Second First Name',
            last_name='Second Last Name',
            date_of_birth=timezone.make_aware(datetime(1950, 2, 3)),
            sex=Patient.SexType.FEMALE,
        )

        # create second `HospitalPatient` record
        patient_factories.HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=hospital_settings_factories.Site(code='MGH'),
        )

        message, error = self._call_command('find_patients_deviations')
        assert 'No deviations have been found in the "Patient" tables/models.' in message

    def test_patient_records_deviations_access_level(self) -> None:
        """Ensure the command returns an error if the access level does not match."""
        # create legacy patient
        legacy_patient = legacy_factories.LegacyPatientFactory(
            patientsernum=99,
            ssn='RAMQ12345678',
            firstname='First Name',
            lastname='Last Name',
            dateofbirth=timezone.make_aware(datetime(2018, 1, 1)),
            sex='Male',
            telnum='5149995555',
            email='opal@example.com',
            language='en',
            accesslevel='1',
        )
        caregiver_factories.CaregiverProfile(
            user=user_factories.Caregiver(
                email='opal@example.com',
                language='en',
                phone_number='5149995555',
            ),
            legacy_id=99,
        )
        # create patient
        patient: Patient = patient_factories.Patient(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )

        assert patient.data_access == Patient.DataAccessType.ALL
        assert legacy_patient.accesslevel == '1'

        message, error = self._call_command('find_patients_deviations')

        assert 'found deviations in the "Patient" tables/models!!!' in error


class TestQuestionnaireRespondentsDeviationsCommand(CommandTestMixin):
    """Test class for the custom command that detects `Questionnaire respondents` sync deviations."""

    def test_deviations_no_respondents(self, django_db_blocker: _DatabaseBlocker) -> None:
        """Ensure the command does not fail if there are no questionnaires with respondents."""
        with django_db_blocker.unblock():
            with connections['questionnaire'].cursor() as conn:
                conn.execute('SET FOREIGN_KEY_CHECKS=0; DELETE FROM answerQuestionnaire;')
                conn.close()

        message, error = self._call_command('find_questionnaire_respondent_deviations')
        assert 'No sync errors has been found in the in the questionnaire respondent data.' in message

    def test_questionnaire_respondents_deviations(self, django_db_blocker: _DatabaseBlocker) -> None:
        """Ensure the command detects the deviations between "answerQuestionnaire" table and `CaregiverProfile`."""
        with django_db_blocker.unblock():
            with connections['questionnaire'].cursor() as conn:
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

        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT',
            username='firebase hashed user UID',
        )

        # this user should not be included to the error list
        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT test1',
            username='firebase hashed user UID_1',
        )

        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT test2_2',
            username='firebase hashed user UID_2',
        )

        message, error = self._call_command('find_questionnaire_respondent_deviations')
        assert 'found deviations in the questionnaire respondents!!!' in error
        assert "('', '')" in error
        assert "('firebase hashed user UID_2', 'TEST NAME RESPONDENT test2_2')" in error
        assert "('firebase hashed user UID', 'TEST NAME RESPONDENT test3')" in error
        assert "('firebase hashed user UID_2', 'TEST NAME RESPONDENT test2')" in error

    def test_no_questionnaire_respondents_deviations(self, django_db_blocker: _DatabaseBlocker) -> None:
        """Ensure the command does not return an error if no sync deviations for respondents' names."""
        with django_db_blocker.unblock():
            with connections['questionnaire'].cursor() as conn:
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

        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT',
            username='firebase hashed user UID',
        )

        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT test1',
            username='firebase hashed user UID_1',
        )

        user_factories.User(
            first_name='TEST NAME',
            last_name='RESPONDENT test2',
            username='firebase hashed user UID_2',
        )

        message, error = self._call_command('find_questionnaire_respondent_deviations')
        assert 'No sync errors has been found in the in the questionnaire respondent data.' in message


class TestUpdateOrmsPatientsCommand(CommandTestMixin):
    """Test class for the custom command that updates patients' UUIDs in the ORMS."""

    def test_orms_patients_update_with_no_patients(self) -> None:
        """Ensure the command does not fail if there are no patient records."""
        message, error = self._call_command('update_orms_patients')
        assert 'Updated 0 out of 0 patients.' in message

    def test_orms_patients_update_with_no_hospital_patients(self) -> None:
        """Ensure the command does not fail if there are no hospital patient records (e.g., MRN/site)."""
        # Create patients
        patient_factories.Patient(id=1, ramq='RAMQ11111111')
        patient_factories.Patient(id=2, ramq='RAMQ22222222')
        patient_factories.Patient(id=3, ramq='RAMQ33333333')
        message, error = self._call_command('update_orms_patients')
        assert 'Updated 0 out of 3 patients.' in message

    def test_orms_patients_update_with_request_exception(self, mocker: MockerFixture) -> None:
        """Ensure the command handles exceptions during POST requests to the ORMS."""
        # Create test data
        site = patient_factories.Site(code='RVH')
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
            mrn='9999999',
        )
        # Create mock POST request
        mock_post = RequestMockerTest.mock_requests_post(mocker, {})
        mock_post.side_effect = requests.RequestException('request failed')
        mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
        # Call the command
        message, error = self._call_command('update_orms_patients')

        number_of_patients = Patient.objects.all().count()
        assert error.count("An error occurred during patient's UUID update!") == number_of_patients

    def test_orms_patients_update_unsuccessful_response(self, mocker: MockerFixture) -> None:
        """Ensure the command handles unsuccessful responses during POST requests to the ORMS."""
        # Create test data
        site = patient_factories.Site(code='RVH')
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
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
        site = patient_factories.Site(code='RVH')
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=1, ramq='RAMQ11111111', uuid=uuid.uuid4()),
            mrn='9999996',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=2, ramq='RAMQ22222222', uuid=uuid.uuid4()),
            mrn='9999997',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=3, ramq='RAMQ33333333', uuid=uuid.uuid4()),
            mrn='9999998',
        )
        patient_factories.HospitalPatient(
            site=site,
            patient=patient_factories.Patient(legacy_id=4, ramq='RAMQ44444444', uuid=uuid.uuid4()),
            mrn='9999999',
        )
        # Create mock POST request
        mock_post = RequestMockerTest.mock_requests_post(mocker, {})
        mock_post.return_value.status_code = HTTPStatus.OK
        # Call the command
        message, error = self._call_command('update_orms_patients')

        patients_num = Patient.objects.all().count()
        assert "An error occurred during patients' UUID update!" not in error
        assert 'Updated {0} out of {1}'.format(patients_num, patients_num) in message
        assert 'The following patients were not updated:' not in error
