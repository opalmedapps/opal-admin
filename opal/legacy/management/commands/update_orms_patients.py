"""Command for updating patients' UUIDs in the Online Room Management System (a.k.a. ORMS)."""
from http import HTTPStatus
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

from opal.patients.models import Patient

SPLIT_LENGTH = 120


class Command(BaseCommand):
    """Command to update patients' UUIDs in the ORMS.

    The command goes through all the patients and for each patient calls the ORMS API \
    to inform ORMS about the patient's UUID.
    """

    help = "Update patients' UUIDs in the ORMS"  # noqa: A003
    requires_migrations_checks = True

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle the update of the patients' UUIDs in the ORMS.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        patients = Patient.objects.prefetch_related(
            'hospital_patients__site',
        )
        skipped_patients = []

        for patient in patients:
            hospital_patient = patient.hospital_patients.first()
            if not hospital_patient:
                skipped_patients.append(patient)
                continue

            # Try to send an HTTP POST request and get a response
            try:
                response = requests.post(
                    url='{0}/php/api/public/v2/patient/updateOpalStatus.php'.format(settings.ORMS_HOST),
                    headers={
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'mrn': hospital_patient.mrn,
                        'site': hospital_patient.site.code,
                        'opalStatus': 1,  # Patient.OpalPatient field in the ORMS database
                        'opalUUID': str(patient.uuid),
                    },
                    timeout=5,
                )
            except requests.exceptions.RequestException as req_exp:
                skipped_patients.append(patient)
                # Print an error to the console
                self.stderr.write(
                    '{error_msg}\npatient_id={patient_id}\t\tpatient_uuid={patient_uuid}\n{exp_msg}'.format(
                        error_msg="An error occurred during patient's UUID update!",
                        patient_id=patient.id,
                        patient_uuid=str(patient.uuid),
                        exp_msg=str(req_exp),
                    ),
                )
                continue

            # Add patient to the skipped_patients list if the response status code is not success
            if response.status_code != HTTPStatus.OK:
                skipped_patients.append(patient)

        self.stdout.write('\n\n{0}\n'.format(SPLIT_LENGTH * '-'))
        self.stdout.write(
            'Updated {0} out of {1} patients.'.format(
                patients.count() - len(skipped_patients),
                patients.count(),
            ),
        )

        self._print_skipped_patients(skipped_patients)

    def _print_skipped_patients(self, skipped_patients: list[Patient]) -> None:
        """Print the patients' UUIDs that were not updated in the ORMS.

        Args:
            skipped_patients: patients that were not updated
        """
        if skipped_patients:
            self.stderr.write('\nThe following patients were not updated:\n')
            for skipped_patient in skipped_patients:
                self.stderr.write(
                    'patient_id={patient_id}\t\tpatient_uuid={patient_uuid}\n'.format(
                        patient_id=skipped_patient.id,
                        patient_uuid=str(skipped_patient.uuid),
                    ),
                )
