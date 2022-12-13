"""Command for detecting deviations between MariaDB and Django `Patient` model tables."""
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone

SPLIT_LENGTH = 120


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
            patient_query = """
                SELECT
                    PP.legacy_id AS LegacyID,
                    PP.ramq AS RAMQ,
                    PP.first_name AS FirstName,
                    PP.last_name AS LastName,
                    DATE_FORMAT(PP.date_of_birth, "%Y-%m-%d") AS BirthDate,
                    UPPER(PP.sex) AS Sex,
                    UU.phone_number AS Phone,
                    LOWER(UU.email) AS Email,
                    LOWER(UU.language) AS Language
                FROM patients_patient PP
                LEFT JOIN caregivers_caregiverprofile CC ON PP.legacy_id = CC.legacy_id
                LEFT JOIN users_user UU ON CC.user_id = UU.id;
            """  # noqa: WPS323

            hospital_patient_query = """
            SELECT
                PP.legacy_id AS LegacyID,
                UPPER(HSS.code) AS SiteCode,
                PHP.mrn AS MRN,
                PHP.is_active AS IsActive
            FROM patients_hospitalpatient PHP
            LEFT JOIN patients_patient PP ON PHP.id = PP.id
            LEFT JOIN hospital_settings_site HSS ON PHP.site_id = HSS.id;
            """

            django_db.execute(patient_query)
            django_patient_set = set(django_db.fetchall())
            django_db.execute(hospital_patient_query)
            django_hospital_patient = set(django_db.fetchall())

        with connections['legacy'].cursor() as legacy_db:
            patient_query = """
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
                    TelNum AS Phone,
                    LOWER(Email) AS Email,
                    LOWER(Language) AS Language
                FROM Patient;
            """  # noqa: WPS323

            hospital_patient_query = """
                SELECT
                    PatientSerNum AS LegacyID,
                    UPPER(Hospital_Identifier_Type_Code) AS SiteCode,
                    MRN AS MRN,
                    Is_Active AS IsActive
                FROM Patient_Hospital_Identifier;
            """

            legacy_db.execute(patient_query)
            legacy_patient = legacy_db.fetchall()
            legacy_db.execute(hospital_patient_query)
            legacy_hospital_patient = legacy_db.fetchall()

        # Please see the details about the `symmetric_difference` method in the links below:
        # https://www.geeksforgeeks.org/python-set-symmetric_difference-2/
        # https://www.w3schools.com/python/ref_set_symmetric_difference.asp
        unmatched_patients = django_patient_set.symmetric_difference(legacy_patient)

        unmatched_hospital_patients = django_hospital_patient.symmetric_difference(legacy_hospital_patient)

        if not unmatched_patients and not unmatched_hospital_patients:
            self.stdout.write('No deviations has been found in the "Patient" tables/models.')
            return

        err_str = '\n{0}: found deviations in the "Patient" tables/models!!!'.format(timezone.now())

        if unmatched_patients:
            err_str += '\n\n{0}'.format(SPLIT_LENGTH * '-')
            err_str = '{0}\nOpalDB.Patient  <===>  opal.patients_patient:\n\n'.format(err_str)
            err_str += '\n'.join(str(patient) for patient in (unmatched_patients))
            err_str += '\n{0}'.format(SPLIT_LENGTH * '-')

        if unmatched_hospital_patients:
            err_str += '\n\n{0}'.format(SPLIT_LENGTH * '-')
            err_str = '{0}\nOpalDB.Patient_Hospital_Identifier  <===>  opal.patients_hospitalpatient:\n\n'.format(
                err_str,
            )
            err_str += '\n'.join(str(patient) for patient in (unmatched_hospital_patients))
            err_str += '\n{0}'.format(SPLIT_LENGTH * '-')

        err_str += '\n\n{0}\n{0}'.format(SPLIT_LENGTH * '=')

        self.stderr.write(
            err_str,
        )
