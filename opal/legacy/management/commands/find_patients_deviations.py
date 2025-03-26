"""Command for detecting deviations between MariaDB and Django `Patient` model tables."""
from typing import Any, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone

SPLIT_LENGTH = 120

LEGACY_PATIENT_QUERY = """
    SELECT
        PatientSerNum AS LegacyID,
        SSN AS RAMQ,
        FirstName AS FirstName,
        LastName AS LastName,
        DATE_FORMAT(DateOfBirth, "%Y-%m-%d") AS BirthDate,
        (
        CASE
            WHEN UPPER(Sex) = "M" THEN "M"
            WHEN UPPER(Sex) = "MALE" THEN "M"
            WHEN UPPER(Sex) = "F" THEN "F"
            WHEN UPPER(Sex) = "FEMALE" THEN "F"
            ELSE "UNDEFINED"
        END
        ) AS Sex,
        CONVERT(TelNum, CHAR) AS Phone,
        LOWER(Email) AS Email,
        LOWER(Language) AS Language,
        (
        CASE
            WHEN AccessLevel = "1" THEN "NTK"
            WHEN AccessLevel = "3" THEN "ALL"
            ELSE "UNDEFINED"
        END
        ) As AccessLevel
    FROM Patient;
"""  # noqa: WPS323

LEGACY_HOSPITAL_PATIENT_QUERY = """
    SELECT
        PatientSerNum AS LegacyID,
        UPPER(Hospital_Identifier_Type_Code) AS SiteCode,
        MRN AS MRN,
        Is_Active AS IsActive
    FROM Patient_Hospital_Identifier;
"""

DJANGO_PATIENT_QUERY = """
    SELECT
        PP.legacy_id AS LegacyID,
        PP.ramq AS RAMQ,
        PP.first_name AS FirstName,
        PP.last_name AS LastName,
        DATE_FORMAT(PP.date_of_birth, "%Y-%m-%d") AS BirthDate,
        UPPER(PP.sex) AS Sex,
        UU.phone_number AS Phone,
        LOWER(UU.email) AS Email,
        LOWER(UU.language) AS Language,
        PP.data_access As AccessLevel
    FROM patients_patient PP
    LEFT JOIN caregivers_caregiverprofile CC ON PP.legacy_id = CC.legacy_id
    LEFT JOIN users_user UU ON CC.user_id = UU.id;
"""  # noqa: WPS323

DJANGO_HOSPITAL_PATIENT_QUERY = """
    SELECT
        PP.legacy_id AS LegacyID,
        UPPER(HSS.acronym) AS SiteCode,
        PHP.mrn AS MRN,
        PHP.is_active AS IsActive
    FROM patients_hospitalpatient PHP
    LEFT JOIN patients_patient PP ON PHP.patient_id = PP.id
    LEFT JOIN hospital_settings_site HSS ON PHP.site_id = HSS.id;
"""


class Command(BaseCommand):
    """Command to find differences in data between legacy database and new back end database for the `Patient` model.

    The command compares:

        - `OpalDB.Patient` table against `opal.patients_patient` table
        - `OpalDB.Patient_Hospital_Identifier` table against `opal.patients_hospitalpatient` table

    by using Django's models.
    """

    help = 'Check the legacy and new back end databases for the data deviations in the `Patient` tables.'  # noqa: A003
    requires_migrations_checks = True

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Handle deviation check for the `Patient` model tables.

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

        with connections['legacy'].cursor() as legacy_db:
            legacy_db.execute(LEGACY_PATIENT_QUERY)
            legacy_patients = legacy_db.fetchall()
            legacy_db.execute(LEGACY_HOSPITAL_PATIENT_QUERY)
            legacy_hospital_patients = legacy_db.fetchall()

        patients_err_str = self._get_patient_deviations_err(
            django_patients,
            django_hospital_patients,
            legacy_patients,
            legacy_hospital_patients,
        )

        if patients_err_str:
            self.stderr.write(
                patients_err_str,
            )
        else:
            self.stdout.write('No deviations have been found in the "Patient" tables/models.')

    def _get_patient_deviations_err(  # noqa: WPS210
        self,
        django_patients: List[Tuple],
        django_hospital_patients: List[Tuple],
        legacy_patients: List[Tuple],
        legacy_hospital_patients: List[Tuple],
    ) -> Optional[str]:
        """Build error string based on the `Patient` table/model records deviations.

        Args:
            django_patients: Django `Patient` model records
            django_hospital_patients: `HospitalPatient` model records
            legacy_patients: legacy `Patient` table records
            legacy_hospital_patients: legacy `Patient_Hospital_Identifier` table records

        Returns:
            str: error with the `Patient` tables/models deviations if there are any, empty string otherwise
        """
        # Please see the details about the `symmetric_difference` method in the links below:
        # https://www.geeksforgeeks.org/python-set-symmetric_difference-2/
        # https://www.w3schools.com/python/ref_set_symmetric_difference.asp
        django_patients_set = set(django_patients)
        django_hospital_patients_set = set(django_hospital_patients)
        unmatched_patients = django_patients_set.symmetric_difference(legacy_patients)
        unmatched_hospital_patients = django_hospital_patients_set.symmetric_difference(legacy_hospital_patients)

        django_patients_len = len(django_patients_set)
        legacy_patients_len = len(legacy_patients)
        django_hospital_patients_len = len(django_hospital_patients_set)
        legacy_hospital_patients_len = len(legacy_hospital_patients)

        # return `None` if there are no unmatched patients
        # and the number of the data records is the same
        if (
            not unmatched_patients
            and not unmatched_hospital_patients
            and django_patients_len == legacy_patients_len
            and django_hospital_patients_len == legacy_hospital_patients_len
        ):
            return None

        err_str = '\n{0}: found deviations in the "Patient" tables/models!!!'.format(timezone.now())

        # Add an error to the error string if the number of the "Patient" records does not match
        if django_patients_len != legacy_patients_len:
            err_str += '\n\n{0}\n"opal.patients_patient": {1}\n"OpalDB.Patient": {2}'.format(
                'The number of records in "opal.patients_patient" and "OpalDB.Patient" tables does not match!',
                django_patients_len,
                legacy_patients_len,
            )

        # Add an error to the error string if the number of the "HospitalPatient" records does not match
        if django_hospital_patients_len != legacy_hospital_patients_len:
            err_msg = 'The number of records in "opal.patients_hospitalpatient" {0}'.format(
                'and "OpalDB.Patient_Hospital_Identifier" tables does not match!',
            )
            err_str += '\n\n{0}\n{1}: {2}\n{3}: {4}'.format(
                err_msg,
                'opal.patients_hospitalpatient',
                django_hospital_patients_len,
                'OpalDB.Patient_Hospital_Identifier',
                legacy_hospital_patients_len,
            )

        # Add a list of unmatched "Patients" to the error string
        err_str += self._get_unmatched_records_str(
            unmatched_patients,
            'OpalDB.Patient  <===>  opal.patients_patient',
        )

        # Add a list of unmatched "HospitalPatients" to the error string
        err_str += self._get_unmatched_records_str(
            unmatched_hospital_patients,
            'OpalDB.Patient_Hospital_Identifier  <===>  opal.patients_hospitalpatient',
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
        if (unmatched_records):
            return '{0}\n{1}:\n\n{2}{3}'.format(
                '\n\n{0}'.format(SPLIT_LENGTH * '-'),
                block_name,
                '\n'.join(str(patient) for patient in (unmatched_records)),
                '\n{0}'.format(SPLIT_LENGTH * '-'),
            )

        return ''
