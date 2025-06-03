# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing model factories for databank app models."""

import string

from django.utils import timezone

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from opal.patients.factories import Patient

from . import models


class DatabankConsent(DjangoModelFactory[models.DatabankConsent]):
    """Model factory to create [opal.databank.models.DatabankConsent][] models."""

    patient = factory.SubFactory(Patient)
    guid = FuzzyText(length=64, chars=string.ascii_uppercase + string.digits)
    has_appointments = factory.Faker('boolean')
    has_diagnoses = factory.Faker('boolean')
    has_demographics = factory.Faker('boolean')
    has_labs = factory.Faker('boolean')
    has_questionnaires = factory.Faker('boolean')
    last_synchronized = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.DatabankConsent


class SharedData(DjangoModelFactory[models.SharedData]):
    """Model factory to create [opal.databank.models.SharedData][] models."""

    databank_consent = factory.SubFactory(DatabankConsent)
    sent_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    data_id = factory.Sequence(lambda number: number + 1)
    data_type = factory.Iterator(models.DataModuleType.values)  # type: ignore[misc]

    class Meta:
        model = models.SharedData
