"""Statistics queries used by usage statistics app."""
from typing import Any

from django.db import models
from django.utils import timezone

from opal.caregivers import models as caregivers_models
from opal.patients import models as patients_models

# GROUP REPORTING - POPULATION-LEVEL AGGREGATE STATISTICS


# Population Summary
def fetch_population_summary() -> dict[str, Any]:
    """Fetch grouped user/patient population summary.

    Returns:
        dictionary with aggregated summaries
    """
    incomplete_registration_statuses = [
        caregivers_models.RegistrationCodeStatus.NEW,
        caregivers_models.RegistrationCodeStatus.EXPIRED,
        caregivers_models.RegistrationCodeStatus.BLOCKED,
    ]

    return caregivers_models.RegistrationCode.objects.select_related(
        'relationship__patient',
        'relationship__caregiver__user',
    ).filter(
        created_at__date=timezone.now().date(),
    ).aggregate(
        patient_signed_up=models.Count('id'),
        incomplete_registration=models.Count(
            'id',
            filter=models.Q(status__in=incomplete_registration_statuses),
        ),
        completed_registration=models.Count(
            'id',
            filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
        english=models.Count(
            'id',
            filter=models.Q(relationship__caregiver__user__language='en'),
        ),
        french=models.Count(
            'id',
            filter=models.Q(relationship__caregiver__user__language='fr'),
        ),
        deceased=models.Count(
            'id',
            filter=models.Q(relationship__patient__date_of_death__isnull=False),
        ),
        male=models.Count(
            'id',
            filter=models.Q(relationship__patient__sex=patients_models.SexType.MALE),
        ),
        female=models.Count(
            'id',
            filter=models.Q(relationship__patient__sex=patients_models.SexType.FEMALE),
        ),
        other_sex=models.Count(
            'id',
            filter=models.Q(relationship__patient__sex=patients_models.SexType.OTHER),
        ),
        unknown_sex=models.Count(
            'id',
            filter=models.Q(relationship__patient__sex=patients_models.SexType.UNKNOWN),
        ),
        full_access=models.Count(
            'id',
            filter=models.Q(relationship__patient__data_access=patients_models.DataAccessType.ALL),
        ),
        limit_access=models.Count(
            'id',
            filter=models.Q(relationship__patient__data_access=patients_models.DataAccessType.NEED_TO_KNOW),
        ),
    )
