# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing model factories for usage statistics app models."""

import datetime as dt

from django.utils import timezone

import factory
from factory import lazy_attribute
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient, Relationship
from opal.users.factories import Caregiver

from . import models


class DailyUserAppActivity(DjangoModelFactory[models.DailyUserAppActivity]):
    """Model factory to create [opal.usage_statistics.models.DailyUserAppActivity][] models."""

    action_by_user = factory.SubFactory(Caregiver)
    last_login = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    count_logins = factory.Faker('pyint', min_value=0, max_value=20)
    count_feedback = factory.Faker('pyint', min_value=0, max_value=10)
    count_update_security_answers = factory.Faker('pyint', min_value=0, max_value=10)
    count_update_passwords = factory.Faker('pyint', min_value=0, max_value=10)
    count_update_language = factory.Faker('pyint', min_value=0, max_value=10)
    count_device_ios = factory.Faker('pyint', min_value=0, max_value=5)
    count_device_android = factory.Faker('pyint', min_value=0, max_value=5)
    count_device_browser = factory.Faker('pyint', min_value=0, max_value=5)
    action_date = lazy_attribute(lambda _x: timezone.now().date() - dt.timedelta(days=1))

    class Meta:
        model = models.DailyUserAppActivity


class DailyUserPatientActivity(DjangoModelFactory[models.DailyUserPatientActivity]):
    """Model factory to create [opal.usage_statistics.models.DailyUserPatientActivity][] models."""

    user_relationship_to_patient = factory.SubFactory(Relationship)
    action_by_user = factory.SubFactory(Caregiver)
    patient = factory.SubFactory(Patient)
    count_checkins = factory.Faker('pyint', min_value=0, max_value=10)
    count_documents = factory.Faker('pyint', min_value=0, max_value=10)
    count_educational_materials = factory.Faker('pyint', min_value=0, max_value=10)
    count_questionnaires_complete = factory.Faker('pyint', min_value=0, max_value=10)
    count_labs = factory.Faker('pyint', min_value=0, max_value=20)
    action_date = lazy_attribute(lambda _x: timezone.now().date() - dt.timedelta(days=1))

    class Meta:
        model = models.DailyUserPatientActivity


class DailyPatientDataReceived(DjangoModelFactory[models.DailyPatientDataReceived]):
    """Model factory to create [opal.usage_statistics.models.DailyPatientDataReceived][] models."""

    patient = factory.SubFactory(Patient)
    next_appointment = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    last_appointment_received = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    appointments_received = factory.Faker('pyint', min_value=0, max_value=5)
    last_document_received = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    documents_received = factory.Faker('pyint', min_value=0, max_value=20)
    last_educational_material_received = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    educational_materials_received = factory.Faker('pyint', min_value=0, max_value=20)
    last_questionnaire_received = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    questionnaires_received = factory.Faker('pyint', min_value=0, max_value=20)
    last_lab_received = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    labs_received = factory.Faker('pyint', min_value=0, max_value=50)
    action_date = lazy_attribute(lambda _x: timezone.now().date() - dt.timedelta(days=1))

    class Meta:
        model = models.DailyPatientDataReceived
