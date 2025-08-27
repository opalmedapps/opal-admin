# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Management command for deleting the caregiver user profile and patient data."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from opal.caregivers.models import CaregiverProfile, Device, SecurityAnswer
from opal.patients.models import HospitalPatient, Patient, Relationship
from opal.pharmacy.models import (
    PharmacyComponent,
    PharmacyEncodedOrder,
    PharmacyRoute,
    PhysicianPrescriptionOrder,
)
from opal.questionnaires.models import QuestionnaireProfile
from opal.test_results.models import GeneralTest, LabObservation, Note, PathologyObservation
from opal.usage_statistics.models import (
    DailyPatientDataReceived,
    DailyUserAppActivity,
    DailyUserPatientActivity,
)
from opal.users.models import User


class Command(BaseCommand):
    """
    Command to delete the caregiver data in the database.

    The command delete caregiver profile, user, relationship, related patient data.
    """

    help = 'Delete caregiver profile and related data, includes relationships, users, patient.'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            'ramq',
            type=str,
            help='The medicalcare number of the user that will be deleted',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Backup and delete the caregiver user profile and patient data.

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        ramq = options['ramq']

        # Check if the patient and the self caregiver exist in the system
        patient = Patient.objects.filter(ramq=ramq).first()
        if not patient:
            self.stderr.write(self.style.ERROR('Patient not found.'))
            return

        self_relationship = Relationship.objects.filter(patient=patient, type__name='Self').first()
        if not self_relationship:
            self.stderr.write(self.style.ERROR('The given patient is not an Opal user.'))
            return

        caregiver = self_relationship.caregiver

        self._backup_user_data(patient, caregiver)
        self._remove_user_data(patient, caregiver)
        self.stdout.write(self.style.SUCCESS('The account deletion is completed!'))

    def _backup_user_data(self, patient: Patient, caregiver: CaregiverProfile) -> None:
        """
        Backup the caregiver patient data completely from the database in form of json file.

        Args:
            patient: the selected patient
            caregiver: the self caregiver profile of the patient
        """
        # Backup the user information
        self.stdout.write('Backuping user data...')
        user = caregiver.user
        patient_data = {}
        # Caregiver module and patient module
        patient_data['patient'] = self._transfer_data_to_string(
            next(iter(Patient.objects.filter(ramq=patient.ramq).values()))
        )
        patient_data['user'] = self._transfer_data_to_string(next(iter(User.objects.filter(id=user.id).values())))
        patient_data['caregiver_profile'] = self._transfer_data_to_string(
            next(iter(CaregiverProfile.objects.filter(id=caregiver.id).values()))
        )
        patient_data['relationships'] = self._transfer_data_to_string(
            next(iter(Relationship.objects.filter(patient=patient).values()))
        )
        patient_data['hopital_patient'] = list(HospitalPatient.objects.filter(patient=patient).values())
        patient_data['security_answer'] = list(SecurityAnswer.objects.filter(user=caregiver).values())
        patient_data['device'] = [
            self._transfer_data_to_string(data) for data in list(Device.objects.filter(caregiver=caregiver).values())
        ]

        # Pharmacy module data
        patient_data['physician_prescription_order'] = [
            self._transfer_data_to_string(data)
            for data in list(PhysicianPrescriptionOrder.objects.filter(patient=patient).values())
        ]
        prescription_order_id = [order['id'] for order in patient_data['physician_prescription_order']]
        patient_data['pharmacy_encoded_order'] = [
            self._transfer_data_to_string(data)
            for data in list(
                PharmacyEncodedOrder.objects.filter(physician_prescription_order_id__in=prescription_order_id).values()
            )
        ]
        encoded_order_id = [order['id'] for order in patient_data['pharmacy_encoded_order']]
        patient_data['pharmacy_component'] = [
            self._transfer_data_to_string(data)
            for data in list(PharmacyComponent.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id).values())
        ]
        patient_data['pharmacy_route'] = [
            self._transfer_data_to_string(data)
            for data in list(PharmacyRoute.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id).values())
        ]

        # Questionnaire module data
        patient_data['questionnaire'] = [
            self._transfer_data_to_string(data)
            for data in list(QuestionnaireProfile.objects.filter(user=user).values())
        ]

        # Test results module data
        patient_data['general_test'] = [
            self._transfer_data_to_string(data) for data in list(GeneralTest.objects.filter(patient=patient).values())
        ]
        general_test_id_list = [test['id'] for test in patient_data['general_test']]
        patient_data['note'] = [
            self._transfer_data_to_string(data)
            for data in list(Note.objects.filter(general_test_id__in=general_test_id_list).values())
        ]
        patient_data['lab_observation'] = [
            self._transfer_data_to_string(data)
            for data in list(LabObservation.objects.filter(general_test_id__in=general_test_id_list).values())
        ]
        patient_data['pathology_observation'] = [
            self._transfer_data_to_string(data)
            for data in list(PathologyObservation.objects.filter(general_test_id__in=general_test_id_list).values())
        ]

        # Usage statistics module data
        patient_data['daily_patient_data_received'] = [
            self._transfer_data_to_string(data)
            for data in list(DailyPatientDataReceived.objects.filter(patient=patient).values())
        ]
        patient_data['daily_user_app_activity'] = [
            self._transfer_data_to_string(data)
            for data in list(DailyUserAppActivity.objects.filter(action_by_user_id=user).values())
        ]
        patient_data['daily_user_patient_activity'] = [
            self._transfer_data_to_string(data)
            for data in list(DailyUserPatientActivity.objects.filter(action_by_user_id=user).values())
        ]

        # Save the data into a file
        with Path(f'{patient.ramq}.json').open('w', encoding='utf-8') as backup_file:
            json.dump(patient_data, backup_file, indent=4)

        self.stdout.write('The user Data is successfully backuped from the system!')

    def _remove_user_data(self, patient: Patient, caregiver: CaregiverProfile) -> None:
        """
        Remove the caregiver patient data completely from the database.

        Args:
            patient: the selected patient
            caregiver: the self caregiver profile of the patient
        """
        # Removing patient data
        self.stdout.write('Start removing user data from the system...')
        user = caregiver.user

        # Usage statistics module
        DailyPatientDataReceived.objects.filter(patient=patient).delete()
        DailyUserAppActivity.objects.filter(action_by_user_id=user).delete()
        DailyUserPatientActivity.objects.filter(action_by_user_id=user).delete()

        # Test results module
        general_test_query = GeneralTest.objects.filter(patient=patient)
        general_test_id_list = [test['id'] for test in list(general_test_query.values())]
        PathologyObservation.objects.filter(general_test_id__in=general_test_id_list).delete()
        LabObservation.objects.filter(general_test_id__in=general_test_id_list).delete()
        Note.objects.filter(general_test_id__in=general_test_id_list).delete()
        general_test_query.delete()

        # Questionnaire module
        QuestionnaireProfile.objects.filter(user=user).delete()

        # Pharmacy module
        physician_prescription_order_query = PhysicianPrescriptionOrder.objects.filter(patient=patient)
        prescription_order_id = [order['id'] for order in list(physician_prescription_order_query.values())]
        pharmacy_encoded_order_query = PharmacyEncodedOrder.objects.filter(
            physician_prescription_order_id__in=prescription_order_id
        )
        encoded_order_id = [order['id'] for order in list(pharmacy_encoded_order_query.values())]
        PharmacyRoute.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id).delete()
        PharmacyComponent.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id).delete()
        pharmacy_encoded_order_query.delete()
        physician_prescription_order_query.delete()

        # Caregiver module and patient module
        Device.objects.filter(caregiver=caregiver).delete()
        SecurityAnswer.objects.filter(user=caregiver).delete()
        HospitalPatient.objects.filter(patient=patient).delete()
        Relationship.objects.filter(patient=patient).delete()
        CaregiverProfile.objects.filter(id=caregiver.id).delete()
        User.objects.filter(id=user.id).delete()
        Patient.objects.filter(id=patient.id).delete()

        self.stdout.write('The user data is successfully removed from the system!')

    def _transfer_data_to_string(self, data: Any) -> Any:
        """
        Check if the input data fields are all strings. If not, transfer it to string.

        Args:
            data: the input data

        Returns:
            the data map where the fields are string
        """
        for key, value in data.items():
            if isinstance(value, datetime):
                data.update({key: value.strftime('%Y-%m-%d %H:%M:%S')})
            elif isinstance(value, date):
                data.update({key: value.strftime('%Y-%m-%d')})
            elif not isinstance(value, str):
                data.update({key: str(value)})

        return data
