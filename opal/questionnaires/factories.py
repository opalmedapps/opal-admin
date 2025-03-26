"""Module providing model factories for questionnaire app models."""

from factory import SubFactory
from factory.django import DjangoModelFactory

from opal.users.factories import User

from . import models


class QuestionnaireProfile(DjangoModelFactory):
    """Model factory to create [opal.questionnaires.models.QuestionnaireProfile][] models."""

    class Meta:
        model = models.QuestionnaireProfile

    user = SubFactory(User)
    questionnaire_list = {'19': {'title': 'Opal Feedback Questionnaire', 'lastviewed': '2022-11-17'}}
