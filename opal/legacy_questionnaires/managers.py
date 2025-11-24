# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module providing legacy questionnaire model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.db import connections, models, transaction
from django.db.backends.utils import CursorWrapper
from django.utils import timezone

from opal.patients.models import RelationshipType

if TYPE_CHECKING:
    from .models import LegacyAnswerQuestionnaire, LegacyQuestionnaire

# Logger instance declared at the module level
logger = logging.getLogger(__name__)


class LegacyQuestionnaireManager(models.Manager['LegacyQuestionnaire']):
    """legacy questionnaire manager."""

    def new_questionnaires(
        self,
        patient_sernum: int,
        username: str,
        purpose_id: int,
    ) -> models.QuerySet['LegacyQuestionnaire']:
        """
        Get the queryset of new questionnaires for a given user.

        Note the input sernum for this query is the OpalDB PatientSerNum, we use the
        foreign key relationship from LegacyAnswerQuestionnaire-->LegacyPatient
        to retrieve the proper value (stored as `externalid` in the LegacyPatient model).

        SQL Joins with Django ORM:
            https://docs.djangoproject.com/en/4.1/topics/db/queries/#spanning-multi-valued-relationships

        Args:
            patient_sernum: OpalDB.Patient.PatientSerNum
            username: login user name
            purpose_id: 1 = CLINICAL, 2 = RESEARCH, 3 = QUALITY, 4 = CONSENT, 5 = CLERICAL, 6 = OPAL

        Returns:
            Queryset of new questionnaires.
        """
        respondent_contents = []
        relationship_types = RelationshipType.objects.filter(
            relationship__caregiver__user__username=username,
            relationship__patient__legacy_id=patient_sernum,
        )

        if relationship_types:
            # Always include patient questionnaires, whether the user is the patient themselves or a caregiver.
            respondent_contents.append('Patient')

            # A caregiver user can also access respondent=CAREGIVER questionnaires.
            if relationship_types.exclude(role_type='SELF'):
                respondent_contents.append('Caregiver')

        return self.filter(
            # 0 = New questionnaires
            legacyanswerquestionnaire__status=0,
            legacyanswerquestionnaire__patient__external_id=patient_sernum,
            # questionnaire purpose
            purpose=purpose_id,
            respondent__title__content__in=respondent_contents,
            respondent__title__language_id=2,  # set English as default
        )


class LegacyAnswerQuestionnaireManager(models.Manager['LegacyAnswerQuestionnaire']):
    """LegacyAnswerQuestionnaire manager."""

    @transaction.atomic
    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the latest de-identified questionnaire data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy QuestionnaireDB external_id
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Questionnaire answer data

        """
        # First sql file contains construction of the temporary questionnaire details table
        query_dir_details = Path(__file__).parent / 'sql/databank_questionnaires_details.sql'
        # Second sql file queries from the temp table in conjunction with the 7 answer type tables
        query_dir_answer = Path(__file__).parent / 'sql/databank_questionnaires_answer.sql'

        # Execute SQL contents
        with connections['questionnaire'].cursor() as conn:
            conn.execute(
                self._read_local_sql(query_dir_details),
                [patient_ser_num, timezone.make_naive(last_synchronized)],
            )
            conn.execute(self._read_local_sql(query_dir_answer))
            return self._fetch_all_as_dict(conn)

    def _fetch_all_as_dict(self, cursor: CursorWrapper) -> list[dict[str, Any]]:
        """
        Return all rows from a cursor as a dict.

        Args:
            cursor: Database connection.

        Returns:
            dictionary list for query.

        """
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    def _read_local_sql(self, directory: Path) -> str:
        """
        Open and read SQL content from a local directory.

        Args:
            directory: Path object pointing to location of SQL to be read

        Returns:
            sql string content
        """
        with Path(directory).open(encoding='utf-8') as handle:
            sql_content = handle.read()
            handle.close()
        return sql_content
