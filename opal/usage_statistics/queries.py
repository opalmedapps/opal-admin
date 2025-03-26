"""Statistics queries used by usage statistics app."""
import datetime as dt
from typing import Any

from django.conf import settings
from django.db import models

from opal.caregivers import models as caregivers_models
from opal.patients import models as patients_models

# GROUP REPORTING - POPULATION-LEVEL AGGREGATE STATISTICS


def fetch_registration_summary(
    start_datetime_period: dt.datetime,
    end_datetime_period: dt.datetime,
) -> dict[str, Any]:
    """Fetch grouped registration summary from `RegistrationCode` model.

    Args:
        start_datetime_period: the beginning of the time period of the registration summary
        end_datetime_period: the end of the time period of the registration summary

    Returns:
        registration summary for a given time period
    """
    incomplete_registration_statuses = [
        caregivers_models.RegistrationCodeStatus.NEW,
        caregivers_models.RegistrationCodeStatus.EXPIRED,
        caregivers_models.RegistrationCodeStatus.BLOCKED,
    ]

    return caregivers_models.RegistrationCode.objects.filter(
        created_at__gte=start_datetime_period,
        created_at__lt=end_datetime_period,
    ).aggregate(
        uncompleted_registration=models.Count(
            'id',
            filter=models.Q(status__in=incomplete_registration_statuses),
        ),
        completed_registration=models.Count(
            'id',
            filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
    )


def fetch_opal_users_summary(
    start_datetime_period: dt.datetime,
    end_datetime_period: dt.datetime,
) -> dict[str, Any]:
    """Fetch grouped Opal users summary from `CaregiverProfile` model.

    Args:
        start_datetime_period: the beginning of the time period of the users summary
        end_datetime_period: the end of the time period of the users summary

    Returns:
        Opal users summary for a given time period
    """
    lang_codes = [lang[0] for lang in settings.LANGUAGES]
    lang_dict = {
        lang: models.Count('id', filter=models.Q(user__language=lang)) for lang in lang_codes
    }
    return caregivers_models.CaregiverProfile.objects.filter(
        user__date_joined__gte=start_datetime_period,
        user__date_joined__lt=end_datetime_period,
    ).aggregate(
        total=models.Count('id'),
        **lang_dict,
    )


def fetch_patients_summary(
    start_datetime_period: dt.datetime,
    end_datetime_period: dt.datetime,
) -> dict[str, Any]:
    """Fetch grouped patients summary from `Patient` model.

    Args:
        start_datetime_period: the beginning of the time period of the patients summary
        end_datetime_period: the end of the time period of the patients summary

    Returns:
        patients summary for a given time period
    """
    access_types = [access_type[0] for access_type in patients_models.DataAccessType.choices]
    access_dict = {}
    for access_type in access_types:
        key_name = f'{access_type.lower()}_access'
        access_dict[key_name] = models.Count('id', filter=models.Q(data_access=access_type))

    return patients_models.Patient.objects.aggregate(
        deceased=models.Count('id', filter=models.Q(date_of_death__isnull=False)),
        male=models.Count('id', filter=models.Q(sex=patients_models.SexType.MALE)),
        female=models.Count('id', filter=models.Q(sex=patients_models.SexType.FEMALE)),
        other_sex=models.Count('id', filter=models.Q(sex=patients_models.SexType.OTHER)),
        unknown_sex=models.Count('id', filter=models.Q(sex=patients_models.SexType.UNKNOWN)),
        **access_dict,
    )
