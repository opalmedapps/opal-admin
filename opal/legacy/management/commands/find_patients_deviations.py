"""Command for detecting deviations between MariaDB and Django `Patient` model tables."""
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    """Command to find differences in data between legacy database and new back end database for the `Patient` model.

    The command compares:

        - `OpalDB.Patient` table against `opal.patients_patient` table
        - `OpalDB.Patient_Hospital_Identifier` table against `opal.patients_hospitalpatient` table

    by running raw SQL queries.
    """

    help = 'Check the legacy and new back end databases for the data deviations in the `Patient` tables.'  # noqa: A003
    requires_migrations_checks = True

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle deviation check for the `Patient` model tables.

        The SQL queries for finding the unmatched records in two tables are based on the following articles:

            - https://ubiq.co/database-blog/compare-two-tables-mysql/

            - https://www.mysqltutorial.org/compare-two-tables-to-find-unmatched-records-mysql.aspx

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        with connections['default'].cursor() as django_conn:
            with connections['legacy'].cursor() as legacy_conn:
                query = """
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
                    ) AS Gender,
                    TelNum AS Phone,
                    LOWER(Email) AS Email,
                    LOWER(Language) AS Language
                FROM Patient;"""
                legacy_conn.execute(query)

                print(legacy_conn.fetchall())
                self.stdout.write('hello world!')
        # self.stderr.write(
        #     'Patient with sernum: {legacy_id}, does not exist,skipping.'.format(
        #         legacy_id=legacy_user.usertypesernum,
        #     ),
        # )
