"""Command for detecting deviations between legacy (MariaDB) and new (Django) tables/models."""
from typing import Any, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone

SPLIT_LENGTH = 120

LEGACY_PATIENT_QUERY = """
    SELECT
        P.PatientSerNum AS LegacyID,
        P.SSN AS RAMQ,
        P.FirstName AS FirstName,
        P.LastName AS LastName,
        DATE_FORMAT(P.DateOfBirth, "%Y-%m-%d") AS BirthDate,
        (
        CASE
            WHEN UPPER(P.Sex) = "M" THEN "M"
            WHEN UPPER(P.Sex) = "MALE" THEN "M"
            WHEN UPPER(P.Sex) = "F" THEN "F"
            WHEN UPPER(P.Sex) = "FEMALE" THEN "F"
            WHEN UPPER(P.Sex) = "OTHER" THEN "O"
            WHEN UPPER(P.Sex) = "O" THEN "O"
            ELSE "UNDEFINED"
        END
        ) AS Sex,
        (
        CASE
            WHEN P.AccessLevel = "1" THEN "NTK"
            WHEN P.AccessLevel = "3" THEN "ALL"
            ELSE "UNDEFINED"
        END
        ) As AccessLevel,
        P.DeathDate as DeathDate
    FROM PatientControl PC
    LEFT JOIN Patient P ON PC.PatientSerNum = P.PatientSerNum;
"""  # noqa: WPS323

LEGACY_HOSPITAL_PATIENT_QUERY = """
    SELECT
        PatientSerNum AS LegacyID,
        UPPER(Hospital_Identifier_Type_Code) AS SiteCode,
        MRN AS MRN,
        Is_Active AS IsActive
    FROM Patient_Hospital_Identifier;
"""

LEGACY_CAREGIVER_QUERY = """
    SELECT
        P.PatientSerNum AS LegacyID,
        P.FirstName AS FirstName,
        P.LastName AS LastName,
        CONVERT(P.TelNum, CHAR) AS Phone,
        LOWER(P.Email) AS Email,
        LOWER(P.Language) AS Language,
        U.Username as Username
    FROM Users U
    LEFT JOIN Patient P ON P.PatientSerNum = U.UserTypeSerNum;
"""

DJANGO_PATIENT_QUERY = """
    SELECT
        PP.legacy_id AS LegacyID,
        PP.ramq AS RAMQ,
        PP.first_name AS FirstName,
        PP.last_name AS LastName,
        DATE_FORMAT(PP.date_of_birth, "%Y-%m-%d") AS BirthDate,
        UPPER(PP.sex) AS Sex,
        PP.data_access As AccessLevel,
        PP.date_of_death as DeathDate
    FROM patients_patient PP
    WHERE PP.legacy_id IS NOT NULL;
"""  # noqa: WPS323

DJANGO_HOSPITAL_PATIENT_QUERY = """
    SELECT
        PP.legacy_id AS LegacyID,
        UPPER(HSS.code) AS SiteCode,
        PHP.mrn AS MRN,
        PHP.is_active AS IsActive
    FROM patients_hospitalpatient PHP
    LEFT JOIN patients_patient PP ON PHP.patient_id = PP.id
    LEFT JOIN hospital_settings_site HSS ON PHP.site_id = HSS.id;
"""

DJANGO_CAREGIVER_QUERY = """
    SELECT
        CC.legacy_id AS LegacyID,
        UU.first_name AS FirstName,
        UU.last_name AS LastName,
        UU.phone_number AS Phone,
        LOWER(UU.email) AS Email,
        LOWER(UU.language) AS Language,
        UU.username as Username
    FROM caregivers_caregiverprofile CC
    LEFT JOIN users_user UU ON CC.user_id = UU.id
    WHERE CC.legacy_id IS NOT NULL;
"""  # noqa: WPS323


class Command(BaseCommand):
    """Command to find differences in data between legacy and new (Django) databases.

    The command compares:

        - `OpalDB.Patient` table against `opal.patients_patient` table (patients' records)
        - `OpalDB.Patient_Hospital_Identifier` table against `opal.patients_hospitalpatient` table
        - `OpalDB.Users` table against `opal.users_user` table for comparing caregivers' records

    by using Django's models.

    NOTE!!! For the `patients` and `users/caregivers`, the comparison is performed only for fully inserted
    records (e.g., `patients` and `caregivers` that completed registration). This is to avoid/eliminate
    the following scenarios:

        - after access request in Django: new patient (does not exist in the legacy DB --> no legacy_id) &
          new caregiver (does not exist in the legacy DB --> caregiver profile has no legacy_id and
          Caregiver instance has is_active = False)
        - after completion registration: if it is a caregiver who is not a patient themselves,
          there will be a dummy patient in the legacy Patient table.

    To ensure that the queried Patients are fully inserted in the both databases, the following conditions are used:

        - Django: patients where legacy_id is not None
        - legacy: patients where a corresponding entry in PatientControl exists.

    To ensure that the queried Caregivers are fully inserted in the both databases, the following conditions are used:

        - Django: caregiver where is_active is True (or caregiver profile legacy_id is not None)
        - legacy: ensure there is a row in Users table
    """

    help = """
        Check the legacy and new back end databases
        for the data deviations in the `Patient` and `User/Caregiver` tables.
    """  # noqa: A003
    requires_migrations_checks = True

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Handle deviation check for the `Patient` and `User/Caregiver` models/tables.

        The implementation was inspired by the following articles:

            - https://ubiq.co/database-blog/compare-two-tables-mysql/

            - https://www.mysqltutorial.org/compare-two-tables-to-find-unmatched-records-mysql.aspx

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        with connections['default'].cursor() as django_db:
            django_db.execute(DJANGO_PATIENT_QUERY)
            django_patients = django_db.fetchall()
            django_db.execute(DJANGO_HOSPITAL_PATIENT_QUERY)
            django_hospital_patients = django_db.fetchall()
            django_db.execute(DJANGO_CAREGIVER_QUERY)
            django_caregivers = django_db.fetchall()

        with connections['legacy'].cursor() as legacy_db:
            legacy_db.execute(LEGACY_PATIENT_QUERY)
            legacy_patients = legacy_db.fetchall()
            legacy_db.execute(LEGACY_HOSPITAL_PATIENT_QUERY)
            legacy_hospital_patients = legacy_db.fetchall()
            legacy_db.execute(LEGACY_CAREGIVER_QUERY)
            legacy_caregivers = legacy_db.fetchall()

        patients_err_str = self._get_deviations_err(
            django_patients,
            legacy_patients,
            'opal.patients_patient',
            'OpalDB.Patient(UserType="Patient")',
        )

        hospital_patients_err_str = self._get_deviations_err(
            django_hospital_patients,
            legacy_hospital_patients,
            'opal.patients_hospitalpatient',
            'OpalDB.Patient_Hospital_Identifier',
        )

        caregivers_err_str = self._get_deviations_err(
            django_caregivers,
            legacy_caregivers,
            'opal.caregivers_caregiverprofile',
            'OpalDB.Patient(UserType="Caregiver")',
        )

        err = ''.join(
            filter(None, [patients_err_str, hospital_patients_err_str, caregivers_err_str]),
        )

        if err:
            self.stderr.write(
                err,
            )
        else:
            self.stdout.write('No deviations have been found in the "Patient and Caregiver" tables/models.')

    def _get_deviations_err(
        self,
        django_model_records: List[Tuple],
        legacy_table_records: List[Tuple],
        django_model_name: str,
        legacy_table_name: str,
    ) -> Optional[str]:
        """Build error string based on the model/table records deviations.

        Args:
            django_model_records: Django model's records
            legacy_table_records: legacy table records
            django_model_name: name of the Django's model that is being compared against legacy table records
            legacy_table_name: name of the legacy table that is being compared against Django model's records

        Returns:
            str: error with the model/table records' deviations if there are any, empty string otherwise
        """
        # Please see the details about the `symmetric_difference` method in the links below:
        # https://www.geeksforgeeks.org/python-set-symmetric_difference-2/
        # https://www.w3schools.com/python/ref_set_symmetric_difference.asp
        django_records_set = set(django_model_records)
        unmatched_records = django_records_set.symmetric_difference(legacy_table_records)

        django_records_len = len(django_records_set)
        legacy_records_len = len(legacy_table_records)

        # return `None` if there are no unmatched records
        # and the number of the data records is the same
        if (
            not unmatched_records
            and django_records_len == legacy_records_len
        ):
            return None

        err_str = '\n{0}: found deviations between {1} Django model and {2} legacy table!!!'.format(
            timezone.now(),
            django_model_name,
            legacy_table_name,
        )

        # Add an error to the error string if the number of the table/model records does not match
        if django_records_len != legacy_records_len:
            err_str += '\n\nThe number of records in "{0}" and "{1}" tables does not match!'.format(
                django_model_name,
                legacy_table_name,
            )
            err_str += '\n{0}: {1}\n{2}: {3}'.format(
                django_model_name,
                django_records_len,
                legacy_table_name,
                legacy_records_len,
            )

        # Add a list of unmatched records to the error string
        err_str += self._get_unmatched_records_str(
            unmatched_records,
            '{0}  <===>  {1}'.format(django_model_name, legacy_table_name),
        )

        return '{0}\n\n\n'.format(err_str)

    def _get_unmatched_records_str(
        self,
        unmatched_records: set[Tuple],
        block_name: str,
    ) -> str:
        """Create string that lists all the unmatched records.

        Args:
            unmatched_records: set of the records that will be added to the string
            block_name: the name of the block that lists the records

        Returns:
            string containing unmatched_records
        """
        return '{0}\n{1}:\n\n{2}{3}'.format(
            '\n\n{0}'.format(SPLIT_LENGTH * '-'),
            block_name,
            '\n'.join(str(record) for record in (unmatched_records)),
            '\n{0}'.format(SPLIT_LENGTH * '-'),
        )
