"""
Module providing legacy quesitonnaire model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`
"""
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from .models import LegacyQuestionnaire


class LegacyQuestionnaireManager(models.Manager['LegacyQuestionnaire']):
    """legacy questionnaire manager."""

    def new_questionnaires(self, patient_sernum: int) -> models.QuerySet['LegacyQuestionnaire']:
        """Get the queryset of new questionnaires for a given user.

        Note the input sernum for this query is the OpalDB PatientSerNum, we use the
        foreign key relationship from LegacyAnswerQuestionnaire-->LegacyPatient
        to retrieve the proper value (stored as `externalid` in the LegacyPatient model).

        SQL Joins with Django ORM:
            https://docs.djangoproject.com/en/4.1/topics/db/queries/#spanning-multi-valued-relationships

        Args:
            patient_sernum: OpalDB.Patient.PatientSerNum

        Returns:
            Queryset of new questionnaires.
        """
        return self.filter(
            legacyanswerquestionnaire__status=0,                             # 0 = New questionnaires
            legacyanswerquestionnaire__patientid__external_id=patient_sernum,
            purposeid=1,                                                     # 1 = Clinical questionnaire purpose
        )
