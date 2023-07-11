"""Command for sending data to the Databank."""
import json
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.query import QuerySet

from opal.databank.models import DatabankConsent, DataModuleType
from opal.legacy.models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire


class Command(BaseCommand):
    """Command to send the data of consenting databank patients to the external databank."""

    help = "send consenting Patients' data to the databank"  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle sending patients de-identified data to the databank.

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

                # Retrieve patient data for each module type and send all at once
                combined_module_data: dict = {}
                i = 0
                for databank_patient in queryset:
                    databank_data = self._retrieve_databank_data_for_patient(databank_patient, module)
                    if databank_data:
                        nested_databank_data = self._nest_and_serialize_queryset(
                            databank_patient.guid,
                            databank_data,
                            module,
                        )
                        combined_module_data[f'patient{i}'] = nested_databank_data
                        i += 1
                if combined_module_data:
                    print(json.dumps(combined_module_data, default=str))
            else:
                self.stderr.write(
                    f'No patients found consenting to {DataModuleType(module).label} data donation.',
                )

    def _retrieve_databank_data_for_patient(self, databank_patient: DatabankConsent, module: DataModuleType) -> Any:
        """Use model managers to retrieve databank data for a consenting patient.

        Args:
            databank_patient: Patient consenting for this databank module
            module: databank data module enum type

        Raises:
            ValueError: If an invalid DateModuleType value is provided or if a patient is missing the legacy id

        Returns:
            JSON string of the patient's databank information for this module
        """
        if not databank_patient.patient.legacy_id:
            raise ValueError('Legacy ID missing from Databank Patient.')
        match module:
            case DataModuleType.APPOINTMENTS:
                databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.DIAGNOSES:
                databank_data = LegacyDiagnosis.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.DEMOGRAPHICS:
                databank_data = LegacyPatient.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.LABS:
                databank_data = LegacyPatientTestResult.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.QUESTIONNAIRES:
                databank_data = LegacyAnswerQuestionnaire.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case _:
                raise ValueError(f'{module} not a valid databank data type.')

        if databank_data:
            # Serialize, nest, return the data for this patient
            self.stdout.write(
                f'{len(databank_data)} instances of {DataModuleType(module).label} successfully serialized',
            )
            return databank_data
        else:
            self.stdout.write(
                f'No {DataModuleType(module).label} data found for {databank_patient.patient}',
            )

    def _nest_and_serialize_queryset(self, guid: str, queryset: QuerySet, nesting_key: str) -> dict:
        """Pull the GUID to the top element and nest the rest of the qs records into a single dict.

        Args:
            queryset: Databank queryset with one or many rows
            guid: GUID for this databank patient, used as the 'parent' element of the dict
            nesting_key: name of key for the nested data

        Returns:
            Nested dictionary list
        """
        data = list(queryset)
        return {'GUID': guid, nesting_key: data}
