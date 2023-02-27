"""Module providing model factories for Legacy QuestionnaireDB models."""
from datetime import datetime

from django.utils import timezone

from factory import SubFactory
from factory.django import DjangoModelFactory

from . import models


class LegacyDefinitionTableFactory(DjangoModelFactory):
    """DefinitionTable factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyDefinitionTable

    name = 'questionnaire'


class LegacyDictionaryFactory(DjangoModelFactory):
    """Dictionary factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyDictionary

    content = 'Edmonton Symptom Assessment Survey'
    contentid = 10
    tableid = SubFactory(LegacyDefinitionTableFactory)
    languageid = 1
    creationdate = timezone.make_aware(datetime(2022, 9, 27))


class LegacyPurposeFactory(DjangoModelFactory):
    """Purpose factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyPurpose

    title = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)


class LegacyRespondentFactory(DjangoModelFactory):
    """Respondent factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRespondent

    title = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)


class LegacyQuestionnaireFactory(DjangoModelFactory):
    """Questionnaire factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestionnaire

    purposeid = SubFactory(LegacyPurposeFactory)
    respondentid = SubFactory(LegacyRespondentFactory)
    title = SubFactory(LegacyDictionaryFactory)
    nickname = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)
    instruction = SubFactory(LegacyDictionaryFactory)


class LegacyPatientFactory(DjangoModelFactory):
    """Patient factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyPatient

    externalid = 51
    creationdate = timezone.make_aware(datetime(2022, 9, 27))


class LegacyAnswerQuestionnaireFactory(DjangoModelFactory):
    """AnswerQuestionnaire factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerQuestionnaire

    questionnaireid = SubFactory(LegacyQuestionnaireFactory)
    patientid = SubFactory(LegacyPatientFactory)
    status = 0
