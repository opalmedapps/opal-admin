"""
Module providing legacy quesitonnaire model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`
"""
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from .models import LegacyQuestionnaire

from opal.patients.models import RelationshipType


class LegacyQuestionnaireManager(models.Manager['LegacyQuestionnaire']):
    """legacy questionnaire manager."""

    def new_questionnaires(
        self,
        patient_sernum: int,
        user_name: str,
        purpose_id: int,
    ) -> models.QuerySet['LegacyQuestionnaire']:
        """Get the queryset of new questionnaires for a given user.

        Note the input sernum for this query is the OpalDB PatientSerNum, we use the
        foreign key relationship from LegacyAnswerQuestionnaire-->LegacyPatient
        to retrieve the proper value (stored as `externalid` in the LegacyPatient model).

        SQL Joins with Django ORM:
            https://docs.djangoproject.com/en/4.1/topics/db/queries/#spanning-multi-valued-relationships

        Args:
            patient_sernum: OpalDB.Patient.PatientSerNum
            user_name: loggin user name
            purpose_id: 1 = CLINICAL, 2 = RESEARCH, 3 = QUALITY, 4 = CONSENT, 5 = CLERICAL, 6 = OPAL

        Returns:
            Queryset of new questionnaires.
        """
        respondent_contents = []
        relationship_types = RelationshipType.objects.filter(
            relationship__caregiver__user__username=user_name,
            relationship__patient__legacy_id=patient_sernum,
        )

        if relationship_types:
            if relationship_types.filter(can_answer_questionnaire=True):
                respondent_contents.append('Caregiver')
            if not relationship_types.filter(role_type='SELF'):
                respondent_contents.append('Patient')

        return self.filter(
            legacyanswerquestionnaire__status=0,                             # 0 = New questionnaires
            legacyanswerquestionnaire__patient__external_id=patient_sernum,
            purpose=purpose_id,                                            # questionnaire purpose
            respondent__title__content__in=respondent_contents,
            respondent__title__language_id=2,  # set English as default
        )
