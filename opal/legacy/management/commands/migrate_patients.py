"""Command for Patients migration."""
from typing import Any

from django.core.management.base import BaseCommand

from opal.hospital_settings.models import Site
from opal.legacy.models import LegacyPatient, LegacyPatientHospitalIdentifier
from opal.patients.models import HospitalPatient, Patient, SexType


class Command(BaseCommand):
    """Command to migrate patients from legacy DB to the new backend patients."""

    help = 'migrate Patients from legacy DB to the new backend'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate Patients legacy DB to the new backend printout number of patients imported.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        legacy_patients = LegacyPatient.objects.all()
        if not legacy_patients:
            self.stderr.write(
                'No legacy patients exist',
            )
        imported_patients_count = 0
        for legacy_patient in legacy_patients:
            # Import patient,  if already exists in the new backend do nothing
            migrated_patient = Patient.objects.filter(legacy_id=legacy_patient.patientsernum).first()
            if migrated_patient:
                # When a patient already exist in the new backend
                self.stdout.write(
                    'Patient with legacy_id: {patientsernum} already exists, skipping'.format(
                        patientsernum=legacy_patient.patientsernum,
                    ),
                )

            else:
                # If patient does not exist in the new backend migrate it
                migrated_patient = Patient.objects.create(
                    legacy_id=legacy_patient.patientsernum,
                    date_of_birth=legacy_patient.dateofbirth,
                    sex=SexType[legacy_patient.sex.upper()],
                    first_name=legacy_patient.firstname,
                    last_name=legacy_patient.lastname,
                    ramq=legacy_patient.ssn,
                )
                self.stdout.write(
                    'Imported patients, legacy_id: {patientsernum}'.format(
                        patientsernum=legacy_patient.patientsernum,
                    ),
                )
                imported_patients_count += 1
            # Check if a patient has a record in legacy patient hospital identifier
            self.import_patient_identifier(migrated_patient, legacy_patient)

        self.stdout.write(
            f'Number of imported patients is: {imported_patients_count}',
        )

    def import_patient_identifier(self, migrated_patient: Patient, legacy_patient: LegacyPatient) -> None:
        """
        Check if legacy patient has a corresponding record in patient identifier model, then migrates.

        Args:
            migrated_patient: an instance of the migrated new patient.
            legacy_patient: an instance of the legacy patient.

        Return None.
        """
        legacy_patient_identifiers = LegacyPatientHospitalIdentifier.objects.filter(
            patientsernum=legacy_patient.patientsernum,
        )
        if legacy_patient_identifiers:
            for legacy_patient_identifier in legacy_patient_identifiers:
                # Check if new backend model HospitalPatient already has a record for the added patient
                hospital_patient = HospitalPatient.objects.filter(mrn=legacy_patient_identifier.mrn).first()
                if hospital_patient:
                    # when HospitalPatient record already has been migrated
                    self.stdout.write(
                        'Patient identifier legacy_id: {patientsernum}, mrn:{mrn} already exists, skipping'.format(
                            patientsernum=legacy_patient.patientsernum,
                            mrn=legacy_patient_identifier.mrn,
                        ),
                    )
                else:
                    HospitalPatient.objects.create(
                        patient=migrated_patient,
                        site=Site.objects.get(
                            code=legacy_patient_identifier.hospitalidentifiertypecode.code,
                        ),
                        mrn=legacy_patient_identifier.mrn,
                        is_active=legacy_patient_identifier.isactive,
                    )
                    self.stdout.write(
                        'Imported patient_identifier, legacy_id: {patientsernum}, mrn: {mrn}'.format(
                            patientsernum=legacy_patient.patientsernum,
                            mrn=legacy_patient_identifier.mrn,
                        ),
                    )
        else:
            self.stdout.write(
                'Patient identifier for patient with legacy_id: {patientsernum} does not exist, skipping'.format(
                    patientsernum=legacy_patient.patientsernum,
                ),
            )
