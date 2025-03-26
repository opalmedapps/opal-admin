"""Module providing model factories for Legacy QuestionnaireDB models."""
from datetime import datetime

from django.utils import timezone

from factory import Faker, Sequence, SubFactory
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
    content_id = 999999999
    table = SubFactory(LegacyDefinitionTableFactory)
    language_id = 1
    creation_date = timezone.make_aware(datetime(2022, 9, 27))


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

    purpose = SubFactory(LegacyPurposeFactory)
    respondent = SubFactory(LegacyRespondentFactory)
    title = SubFactory(LegacyDictionaryFactory)
    nickname = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)
    instruction = SubFactory(LegacyDictionaryFactory)
    logo = 'pathtologo'
    deleted_by = 'Test User'
    creationdate = timezone.make_aware(datetime(2022, 9, 27))
    created_by = 'Test User'
    updated_by = 'Test User'
    legacyname = 'Test Questionnaire'


class LegacyPatientFactory(DjangoModelFactory):
    """Patient factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyPatient
        django_get_or_create = ('external_id',)

    external_id = 51
    hospital_id = -1
    creation_date = timezone.make_aware(datetime(2022, 9, 27))
    deleted_by = 'Test User'
    created_by = 'Test User'
    updated_by = 'Test User'


class LegacyAnswerQuestionnaireFactory(DjangoModelFactory):
    """AnswerQuestionnaire factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerQuestionnaire

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    patient = SubFactory(LegacyPatientFactory)
    status = 0
    creation_date = timezone.make_aware(datetime(2022, 9, 27))
    deleted_by = 'Test User'
    created_by = 'Test User'
    updated_by = 'Test User'


class LegacyLanguageFactory(DjangoModelFactory):
    """Language factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyLanguage

    iso_lang = 'en'
    name = SubFactory(LegacyDictionaryFactory)
    deleted = False
    deleted_by = ''
    created_by = Faker('name')
    updated_by = Faker('name')


class LegacySectionFactory(DjangoModelFactory):
    """Section factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacySection

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    title = SubFactory(LegacyDictionaryFactory)
    instruction = SubFactory(LegacyDictionaryFactory)
    order = Sequence(lambda number: number)
    deleted = False
    created_by = Faker('name')
    creation_date = timezone.make_aware(datetime(2022, 9, 27))
    updated_by = Faker('name')


class LegacyTypeFactory(DjangoModelFactory):
    """Type factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyType

    description = SubFactory(LegacyDictionaryFactory)
    table = SubFactory(LegacyDefinitionTableFactory)
    sub_table = SubFactory(LegacyDefinitionTableFactory)
    template_table = SubFactory(LegacyDefinitionTableFactory)
    template_sub_table = SubFactory(LegacyDefinitionTableFactory)


class LegacyQuestionFactory(DjangoModelFactory):
    """Question factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestion
        django_get_or_create = ('display', 'definition', 'question', 'type')

    display = SubFactory(LegacyDictionaryFactory)
    definition = SubFactory(LegacyDictionaryFactory)
    question = Sequence(lambda number: number)
    type = SubFactory(LegacyTypeFactory)  # noqa: A003
    version = 1
    parent_id = -1
    private = False
    final = False
    optional_feedback = False
    deleted = False
    creation_date = timezone.make_aware(datetime(2022, 9, 27))
    created_by = Faker('name')
    updated_by = Faker('name')


class LegacyRadioButtonFactory(DjangoModelFactory):
    """RadioButton factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRadioButton

    question = SubFactory(LegacyQuestionFactory)


class LegacyRadioButtonOptionFactory(DjangoModelFactory):
    """RadioButtonOption factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRadioButtonOption

    parent_table = SubFactory(LegacyRadioButtonFactory)
    description = SubFactory(LegacyDictionaryFactory)
    order = Sequence(lambda number: number)


class LegacyCheckboxFactory(DjangoModelFactory):
    """CheckBox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyCheckbox

    question = SubFactory(LegacyQuestionFactory)


class LegacyCheckboxOptionFactory(DjangoModelFactory):
    """CheckBoxOption factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyCheckboxOption

    order = Faker('random_int')
    description = SubFactory(LegacyDictionaryFactory)
    parent_table = SubFactory(LegacyCheckboxFactory)


class LegacyLabelFactory(DjangoModelFactory):
    """Label factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyLabel

    question = SubFactory(LegacyQuestionFactory)


class LegacyLabelOptionFactory(DjangoModelFactory):
    """LabelOption factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyLabelOption

    description = SubFactory(LegacyDictionaryFactory)
    pos_init_x = Faker('random_int')
    pos_init_y = Faker('random_int')
    pos_final_x = Faker('random_int')
    pos_final_y = Faker('random_int')
    intensity = Faker('random_int')
    order = Faker('random_int')
    parent_table = SubFactory(LegacyLabelFactory)


class LegacyQuestionSectionFactory(DjangoModelFactory):
    """Type factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestionSection

    question = SubFactory(LegacyQuestionFactory)
    section = SubFactory(LegacySectionFactory)
    order = Sequence(lambda number: number)
    orientation = 0
    optional = False


class LegacyAnswerSectionFactory(DjangoModelFactory):
    """AnswerSection factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerSection

    answer_questionnaire = SubFactory(LegacyAnswerQuestionnaireFactory)
    section = SubFactory(LegacySectionFactory)


class LegacyAnswerFactory(DjangoModelFactory):
    """Answer factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswer

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    section = SubFactory(LegacySectionFactory)
    question = SubFactory(LegacyQuestionFactory)
    type = SubFactory(LegacyTypeFactory)  # noqa: A003
    answer_section = SubFactory(LegacyAnswerSectionFactory)
    language = SubFactory(LegacyLanguageFactory)
    patient = SubFactory(LegacyPatientFactory)
    answered = Faker('boolean')
    skipped = Faker('boolean')
    deleted = Faker('boolean')
    deleted_by = Faker('word')
    creation_date = timezone.make_aware(datetime(2022, 9, 27))
    created_by = Faker('word')
    updated_by = Faker('word')


class LegacyAnswerSliderFactory(DjangoModelFactory):
    """AnswerSlider factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerSlider

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('pyfloat', positive=True, min_value=1, max_value=10)


class LegacyAnswerTextBoxFactory(DjangoModelFactory):
    """AnswerTextBox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerTextBox

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('text', max_nb_chars=200)


class LegacyAnswerTimeFactory(DjangoModelFactory):
    """AnswerTime factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerTime

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('time')


class LegacyAnswerLabelFactory(DjangoModelFactory):
    """AnswerLabel factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerLabel

    answer = SubFactory(LegacyAnswerFactory)
    selected = 1
    pos_x = Faker('pyint')
    pos_y = Faker('pyint')
    intensity = Faker('pyint')
    value = Faker('pyint')


class LegacyAnswerRadioButtonFactory(DjangoModelFactory):
    """AnswerRadioButton factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerRadioButton

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('random_int')


class LegacyAnswerCheckboxFactory(DjangoModelFactory):
    """AnswerCheckbox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerCheckbox

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('random_int')


class LegacyAnswerDateFactory(DjangoModelFactory):
    """AnswerDate factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerDate

    answer = SubFactory(LegacyAnswerFactory)
    value = timezone.make_aware(datetime(2022, 9, 27))
