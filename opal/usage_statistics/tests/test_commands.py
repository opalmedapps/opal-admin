from datetime import datetime

from django.db import connections
from django.utils import timezone

import pytest
from pytest_django import DjangoDbBlocker

from opal.caregivers import factories as caregiver_factories
from opal.core.test_utils import CommandTestMixin
from opal.patients import factories as patient_factories
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity
from opal.users import factories as user_factories

pytestmark = pytest.mark.django_db(databases=['default', 'report'])


class TestMigrateLegacyUsageStatisticsMigration(CommandTestMixin):
    """Test class for legacy usage statistics data migrations from legacy DB."""

    def test_migrate_legacy_usage_statistics_with_no_legacy_statistics(
        self,
        django_db_blocker: DjangoDbBlocker,
    ) -> None:
        """Test import success but no legacy statistics exist."""
        with django_db_blocker.unblock():
            self._create_legacy_report_table()

            message, error = self._call_command('migrate_legacy_usage_statistics')
            self._clean_legacy_report_table()

        assert 'Number of imported legacy activity log is: 0' in message
        assert 'Number of imported legacy data received log is: 0' in message
        assert DailyUserAppActivity.objects.all().count() == 0
        assert DailyUserPatientActivity.objects.all().count() == 0
        assert DailyPatientDataReceived.objects.all().count() == 0

    def test_migrate_legacy_usage_statistics_with_success(self, django_db_blocker: DjangoDbBlocker) -> None:
        """Ensure the command handle the legacy usage statistics migration with success."""
        with django_db_blocker.unblock():
            self._create_legacy_report_table()
            self._create_test_legacy_usage_statistics()
            self._create_test_self_registered_patient()

            message, error = self._call_command('migrate_legacy_usage_statistics')
            self._clean_legacy_report_table()

        assert 'Number of imported legacy activity log is: 1' in message
        assert 'Number of imported legacy data received log is: 1' in message
        assert DailyUserAppActivity.objects.all().count() == 1
        assert DailyUserPatientActivity.objects.all().count() == 1
        assert DailyPatientDataReceived.objects.all().count() == 1

    def test_migrate_legacy_patient_activity_logs_with_failed(self, django_db_blocker: DjangoDbBlocker) -> None:
        """Test the legacy patient activity log migration failed due to unexisting patient."""
        with django_db_blocker.unblock():
            self._create_legacy_report_table()
            self._create_test_legacy_usage_statistics()
            self._create_test_self_registered_patient()
            with connections['report'].cursor() as conn:
                query = """
                    UPDATE `rpt_patient_activity_log` SET PatientSerNum=100;
                """
                conn.execute(query)
                conn.close()

            message, error = self._call_command('migrate_legacy_usage_statistics')
            self._clean_legacy_report_table()

        assert 'Cannot import patient legacy activity log for patient (legacy ID: 100),' in error
        assert 'Number of imported legacy activity log is: 0' in message
        assert 'Number of imported legacy data received log is: 1' in message

    def test_migrate_legacy_patient_data_received_log_with_failed(self, django_db_blocker: DjangoDbBlocker) -> None:
        """Test the legacy patient data received log migration failed due to unexisting patient."""
        with django_db_blocker.unblock():
            self._create_legacy_report_table()
            self._create_test_legacy_usage_statistics()
            self._create_test_self_registered_patient()
            with connections['report'].cursor() as conn:
                query = """
                    UPDATE `rpt_patient_log` SET PatientSerNum=100;
                    UPDATE `rpt_patient_labs_log` SET PatientSerNum=100;
                """
                conn.execute(query)
                conn.close()

            message, error = self._call_command('migrate_legacy_usage_statistics')
            self._clean_legacy_report_table()

        assert 'Cannot import patient legacy data received log for patient (legacy ID: 100),' in error
        assert 'Number of imported legacy activity log is: 1' in message
        assert 'Number of imported legacy data received log is: 0' in message

    def _create_legacy_report_table(self) -> None:
        """Create legacy report table."""
        with connections['report'].cursor() as conn:
            query = """
                CREATE TABLE `rpt_patient_activity_log` (
                    `ID` BIGINT(20) NOT NULL AUTO_INCREMENT,
                    `PatientSerNum` INT(11) NOT NULL,
                    `Last_Login` DATETIME NULL DEFAULT NULL,
                    `Date_Login` DATE NULL DEFAULT NULL,
                    `Count_Login` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Checkin` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Clinical_Notes` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Educational_Material` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Feedback` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Questionnaire` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Update_Security_Answer` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_LabResults` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Count_Update_Password` DECIMAL(22,0) NULL DEFAULT NULL,
                    `Year_Login` INT(4) NULL DEFAULT NULL,
                    `Month_Login` INT(2) NULL DEFAULT NULL,
                    `Day_Login` INT(2) NULL DEFAULT NULL,
                    `Day_Of_Week_Login` INT(1) NULL DEFAULT NULL,
                    `Date_Added` DATE NOT NULL,
                    PRIMARY KEY (`ID`) USING BTREE,
                    INDEX `PatientSerNum` (`PatientSerNum`) USING BTREE,
                    INDEX `Year_Login` (`Year_Login`) USING BTREE,
                    INDEX `Date_Login` (`Date_Login`) USING BTREE,
                    INDEX `Day_Of_Week_Login` (`Day_Of_Week_Login`) USING BTREE
                )
                COLLATE='latin1_swedish_ci'
                ENGINE=InnoDB;

                CREATE TABLE `rpt_patient_labs_log` (
                    `ID` BIGINT(20) NOT NULL AUTO_INCREMENT,
                    `PatientSerNum` INT(11) NOT NULL,
                    `Last_Lab_Received` DATETIME NULL DEFAULT NULL,
                    `Date_Received` DATE NULL DEFAULT NULL,
                    `Count_Labs` INT(4) NULL DEFAULT NULL,
                    `Year_Received` INT(4) NULL DEFAULT NULL,
                    `Month_Received` INT(2) NULL DEFAULT NULL,
                    `Day_Received` INT(2) NULL DEFAULT NULL,
                    `Day_Of_Week_Received` INT(1) NULL DEFAULT NULL,
                    `Date_Added` DATE NOT NULL,
                    PRIMARY KEY (`ID`) USING BTREE,
                    INDEX `PatientSerNum` (`PatientSerNum`) USING BTREE,
                    INDEX `Date_Received` (`Date_Received`) USING BTREE,
                    INDEX `Year_Received` (`Year_Received`) USING BTREE,
                    INDEX `Day_Of_Week_Received` (`Day_Of_Week_Received`) USING BTREE
                )
                COLLATE='latin1_swedish_ci'
                ENGINE=InnoDB;

                CREATE TABLE `rpt_patient_log` (
                    `ID` BIGINT(20) NOT NULL AUTO_INCREMENT,
                    `Date_Added` DATE NULL DEFAULT NULL,
                    `PatientSerNum` INT(11) NOT NULL DEFAULT '0',
                    `Sex` VARCHAR(25) NOT NULL COLLATE 'latin1_swedish_ci',
                    `Language` ENUM('EN','FR','SN') NOT NULL COLLATE 'latin1_swedish_ci',
                    `AccessLevel` ENUM('1','2','3') NOT NULL DEFAULT '1' COLLATE 'latin1_swedish_ci',
                    `BlockedStatus` TINYINT(4) NOT NULL DEFAULT '0' COMMENT 'to block user on Firebase',
                    `StatusReasonTxt` TEXT NOT NULL COLLATE 'latin1_swedish_ci',
                    `Last_Login` DATETIME NULL DEFAULT NULL,
                    `Last_Appointment_Received` DATETIME NULL DEFAULT NULL,
                    `Next_Appointment` DATETIME NULL DEFAULT NULL,
                    `Last_Lab_Received` DATETIME NULL DEFAULT NULL,
                    `Last_Diagnosis_Received` DATETIME NULL DEFAULT NULL,
                    `Last_Clinical_Notes_Received` DATETIME NULL DEFAULT NULL,
                    `Completed_Registration` VARCHAR(3) NULL DEFAULT 'No' COLLATE 'latin1_swedish_ci',
                    `iOS` INT(11) NULL DEFAULT '0',
                    `Android` INT(11) NULL DEFAULT '0',
                    `Browser` INT(11) NULL DEFAULT '0',
                    PRIMARY KEY (`ID`) USING BTREE,
                    INDEX `Date_Added` (`Date_Added`) USING BTREE,
                    INDEX `PatientSerNum` (`PatientSerNum`) USING BTREE
                )
                COLLATE='latin1_swedish_ci'
                ENGINE=InnoDB;
            """
            conn.execute(query)
            conn.close()

    def _clean_legacy_report_table(self) -> None:
        """Delete legacy report table."""
        with connections['report'].cursor() as conn:
            query = """
                DROP TABLE `rpt_patient_activity_log`;
                DROP TABLE `rpt_patient_labs_log`;
                DROP TABLE `rpt_patient_log`;
            """
            conn.execute(query)
            conn.close()

    def _create_test_legacy_usage_statistics(self) -> None:
        """Create test legacy usage statistics logs."""
        with connections['report'].cursor() as conn:
            query = """
                INSERT INTO rpt_patient_activity_log(
                    `PatientSerNum`,
                    `Last_Login`,
                    `Date_Login`,
                    `Count_Login`,
                    `Count_Checkin`,
                    `Count_Clinical_Notes`,
                    `Count_Educational_Material`,
                    `Count_Feedback`,
                    `Count_Questionnaire`,
                    `Count_Update_Security_Answer`,
                    `Count_LabResults`,
                    `Count_Update_Password`,
                    `Year_Login`,
                    `Month_Login`,
                    `Day_Login`,
                    `Day_Of_Week_Login`,
                    `Date_Added`
                )
                VALUES (99, NOW(), CURRENT_DATE(),0,0,0,0,0,0,0,0,0,0,0,0,0,CURRENT_DATE());

                INSERT INTO rpt_patient_labs_log(
                    `PatientSerNum`,
                    `Last_Lab_Received`,
                    `Date_Received`,
                    `Count_Labs`,
                    `Year_Received`,
                    `Month_Received`,
                    `Day_Received`,
                    `Day_Of_Week_Received`,
                    `Date_Added`
                )
                VALUES (99, NOW(), CURRENT_DATE(),0,0,0,0,0,CURRENT_DATE());

                INSERT INTO rpt_patient_log(
                    `Date_Added`,
                    `PatientSerNum`,
                    `Sex`,
                    `Language`,
                    `AccessLevel`,
                    `BlockedStatus`,
                    `StatusReasonTxt`,
                    `Last_Login`,
                    `Last_Appointment_Received`,
                    `Next_Appointment`,
                    `Last_Lab_Received`,
                    `Last_Diagnosis_Received`,
                    `Last_Clinical_Notes_Received`,
                    `Completed_Registration`,
                    `iOS`,
                    `Android`,
                    `Browser`
                )
                VALUES (CURRENT_DATE(),99,'M','EN','3',0,'Test',NOW(),NOW(),NOW(),NOW(),NOW(),NOW(),'Yes',0,0,0);
            """
            conn.execute(query)
            conn.close()

    def _create_test_self_registered_patient(self) -> None:
        """Create a test self registered patient."""
        patient = patient_factories.Patient(
            legacy_id=99,
            ramq='RAMQ12345678',
            first_name='First Name',
            last_name='Last Name',
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )
        caregiver = caregiver_factories.CaregiverProfile(
            user=user_factories.Caregiver(
                language='en',
                phone_number='5149999999',
                first_name='First Name',
                last_name='Last Name',
                username='first_username',
            ),
            legacy_id=99,
        )
        relationship_type = patient_factories.RelationshipType(name='Self')
        patient_factories.Relationship(
            patient=patient,
            caregiver=caregiver,
            type=relationship_type,
        )
