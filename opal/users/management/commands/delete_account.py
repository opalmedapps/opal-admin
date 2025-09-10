# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Management command for deleting the caregiver user profile and patient data."""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.core.serializers import serialize
from django.db.models.query import QuerySet

from opal.caregivers.models import CaregiverProfile, Device, SecurityAnswer
from opal.patients.models import HospitalPatient, Patient, Relationship, RoleType
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
            'email',
            type=str,
            help='The email of the user that will be deleted',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Backup and delete the caregiver user profile and patient data.

        i.e.,The list is created in the regular order (which is used for recovery),
        the deletion needs to happen in reverse order due to constraints between the model instances.

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        email = options['email']
        # Check if the patient and the self caregiver exist in the system
        caregiver = CaregiverProfile.objects.filter(user__email=email).first()
        if not caregiver:
            self.stderr.write(self.style.ERROR('User not found.'))
            return

        user = caregiver.user
        # Prepare a list of query set for the data that will be backuped and deleted
        query_set_list: list[QuerySet[Any, Any]] = [
            User.objects.filter(pk=user.pk),
            CaregiverProfile.objects.filter(pk=caregiver.pk),
            SecurityAnswer.objects.filter(user=caregiver),
            Device.objects.filter(caregiver=caregiver),
            # Questionnaire module data
            QuestionnaireProfile.objects.filter(user=user),
            # Usage statistics module data for user
            DailyUserAppActivity.objects.filter(action_by_user_id=user),
            DailyUserPatientActivity.objects.filter(action_by_user_id=user),
        ]

        # Prepare the query set for self patient data if the user have a self relationship
        self_relationship = Relationship.objects.filter(caregiver=caregiver, type__role_type=RoleType.SELF).first()
        if self_relationship:
            patient = self_relationship.patient
            query_set_list.extend([
                Patient.objects.filter(pk=patient.pk),
                HospitalPatient.objects.filter(patient=patient),
                Relationship.objects.filter(patient=patient),
            ])
            # Pharmacy module data
            prescription_order = PhysicianPrescriptionOrder.objects.filter(patient=patient)
            prescription_order_id = [order.id for order in prescription_order]
            encoded_order = PharmacyEncodedOrder.objects.filter(
                physician_prescription_order_id__in=prescription_order_id
            )
            encoded_order_id = [order.id for order in encoded_order]
            query_set_list.extend([
                prescription_order,
                encoded_order,
                PharmacyComponent.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id),
                PharmacyRoute.objects.filter(pharmacy_encoded_order_id__in=encoded_order_id),
            ])
            # Test results module data
            general_test = GeneralTest.objects.filter(patient=patient)
            query_set_list.append(general_test)
            general_test_id_list = [test.id for test in general_test]
            query_set_list.extend([
                general_test,
                Note.objects.filter(general_test_id__in=general_test_id_list),
                LabObservation.objects.filter(general_test_id__in=general_test_id_list),
                PathologyObservation.objects.filter(general_test_id__in=general_test_id_list),
                # Usage statistics module data for patient
                DailyPatientDataReceived.objects.filter(patient=patient),
            ])
        # Add the relationship in the end to facilitate the recover
        query_set_list.append(Relationship.objects.filter(caregiver=caregiver))

        self._backup_user_data(query_set_list)
        self._remove_user_data(query_set_list)

    def _backup_user_data(self, query_set_list: list[QuerySet[Any, Any]]) -> None:
        """
        Backup the caregiver patient data completely from the database in form of json file.

        Args:
            query_set_list: the list of query_set for the data to be backuped
        """
        # Backup the user information
        user_data: list[Any] = []
        for query_set in query_set_list:
            user_data.extend([*query_set])
        user_data_json = serialize('json', user_data)
        self.stdout.write(user_data_json)

    def _remove_user_data(self, query_set_list: list[QuerySet[Any, Any]]) -> None:
        """
        Remove the caregiver patient data completely from the database.

        Args:
            query_set_list: the list of query_set for the data to be deleted
        """
        # Removing patient data
        for query_set in reversed(query_set_list):
            query_set.delete()
