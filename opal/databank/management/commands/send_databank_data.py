"""Command for sending data to the Databank."""
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from opal.databank.models import DatabankConsent, DataModuleType
from opal.legacy.models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire


class Command(BaseCommand):
    """Command to send the data of consenting databank patients to the external databank."""

    help = "send consenting Patients' data to the databank"  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle sending Patients deidentified to the databank.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs: variable keyword input arguments.
        """
        consenting_patients_querysets = {
            DataModuleType.APPOINTMENTS: DatabankConsent.objects.filter(has_appointments=True),
            DataModuleType.DIAGNOSES: DatabankConsent.objects.filter(has_diagnoses=True),
            DataModuleType.DEMOGRAPHICS: DatabankConsent.objects.filter(has_demographics=True),
            DataModuleType.LABS: DatabankConsent.objects.filter(has_labs=True),
            DataModuleType.QUESTIONNAIRES: DatabankConsent.objects.filter(has_questionnaires=True),
        }
        for module, queryset in consenting_patients_querysets.items():
            if queryset:
                self.stdout.write(
                    f'Number of {DataModuleType(module).label}-consenting patients is: {queryset.count()}',
                )
                # Iterate over each databank patient and fetch their data, send to OIE
                for databank_patient in queryset:
                    self._retrieve_databank_data_for_patient(databank_patient, module)
            else:
                self.stderr.write(
                    f'No patients found consenting to {DataModuleType(module).label} data donation.',
                )

    def _retrieve_databank_data_for_patient(self, databank_patient: DatabankConsent, module: DataModuleType) -> None:
        """Use model managers to retrieve databank data for a consenting patient.

        Args:
            databank_patient: Patient consenting for this databank module
            module: databank data module enum type

        Raises:
            ValueError: If an invalid DateModuleType value is provided
        """
        match module:
            case 'APPT':
                databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,  # type: ignore[arg-type]
                    last_synchronized=databank_patient.last_synchronized,  # type: ignore[arg-type]
                )
            case 'DIAG':
                databank_data = LegacyDiagnosis.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,  # type: ignore[arg-type]
                    last_synchronized=databank_patient.last_synchronized,  # type: ignore[arg-type]
                )
            case 'DEMO':
                databank_data = LegacyPatient.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,  # type: ignore[arg-type]
                    last_synchronized=databank_patient.last_synchronized,  # type: ignore[arg-type]
                )
            case 'LABS':
                databank_data = LegacyPatientTestResult.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,  # type: ignore[arg-type]
                    last_synchronized=databank_patient.last_synchronized,  # type: ignore[arg-type]
                )
            case 'QSTN':
                # TODO: Because the questionnaires are retrieved using raw sql, the return type
                #       here is a list of dicts instead of a QuerySet. Should a model be made
                #       specifically to store the results of this query?
                databank_data = LegacyAnswerQuestionnaire.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,  # type: ignore[arg-type]
                    last_synchronized=databank_patient.last_synchronized,  # type: ignore[arg-type]
                )
            case _:
                raise ValueError(f'{module} not a valid databank data type.')

        if databank_data:
            # TODO: QSCCD-1095: Serialize data to JSON and send to OIE
            self.stdout.write(
                f'{len(databank_data)} instances of {DataModuleType(module).label} data found,'
                + ' [Temporary print out for test coverage in pipeline]',
            )
        else:
            self.stdout.write(
                f'No {DataModuleType(module).label} data found for {databank_patient.patient}',
            )
