from io import StringIO
from typing import Any

from django.core.management import call_command

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import SecurityAnswer, SecurityQuestion
from opal.hospital_settings import factories as hospital_settings_factories
from opal.legacy import factories as legacy_factories
from opal.patients import factories as patient_factories
from opal.users import factories as user_factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestBasicClass:
    """Basic test class."""

    def _call_command(self, command_name: str, *args: Any, **kwargs: Any) -> tuple[str, str]:
        """
        Test command.

        Args:
            command_name: specify the command name to run
            args: non-keyword input parameter
            kwargs: keywords input parameter

        Returns:
            A tupe of stdour and stderr values.
        """
        out = StringIO()
        err = StringIO()
        call_command(
            command_name,
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()


class TestSecurityQuestionsMigration(TestBasicClass):
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
        assert question[0].title_en == 'What is the name of your first pet?'
        assert message == (
            'Imported security question, sernum: 1, title: What is the name of your first pet?\n'
        )
        assert error == ''


class TestSecurityAnswersMigration(TestBasicClass):
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


class TestPatientAndPatientIdentifierMigration(TestBasicClass):
    """Test class for security answers migration."""

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

    def test_import_pass_multiple_patientidentifiers(self) -> None:
        """Test import fail for patient and pass multiple patient identifier."""
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
        assert 'Imported patient_identifier, legacy_id: 10, mrn: 9999997\n' in message
        assert 'Number of imported patients is: 0\n' in message
