"""Statistics queries used by usage statistics app."""
import datetime as dt
from typing import Any

from django.conf import settings
from django.db import models

from opal.caregivers import models as caregivers_models
from opal.patients import models as patients_models

# GROUP REPORTING - POPULATION-LEVEL AGGREGATE STATISTICS


def fetch_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch grouped registration summary from `RegistrationCode` model.

    Args:
        start_date: the beginning of the time period of the registration summary (inclusive)
        end_date: the end of the time period of the registration summary (inclusive)

    Returns:
        registration summary for a given time period
    """
    incomplete_registration_statuses = [
        caregivers_models.RegistrationCodeStatus.NEW,
        caregivers_models.RegistrationCodeStatus.EXPIRED,
        caregivers_models.RegistrationCodeStatus.BLOCKED,
    ]

    return caregivers_models.RegistrationCode.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
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


def fetch_caregivers_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch grouped caregivers summary from `CaregiverProfile` model.

    Args:
        start_date: the beginning of the time period of the users summary (inclusive)
        end_date: the end of the time period of the users summary (inclusive)

    Returns:
        caregivers summary for a given time period
    """
    lang_codes = [lang[0] for lang in settings.LANGUAGES]
    lang_dict = {
        lang: models.Count('id', filter=models.Q(user__language=lang)) for lang in lang_codes
    }

    return caregivers_models.CaregiverProfile.objects.filter(
        user__date_joined__gte=start_date,
        user__date_joined__lte=end_date,
    ).aggregate(
        total=models.Count('id'),
        **lang_dict,
    )


def fetch_patients_summary(
    start_date: dt.datetime,
    end_date: dt.datetime,
) -> dict[str, Any]:
    """Fetch grouped patients summary from `Patient` model.

    Args:
        start_date: the beginning of the time period of the patients summary (inclusive)
        end_date: the end of the time period of the patients summary (inclusive)

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
