"""Module providing model factories for Legacy QuestionnaireDB models."""

from datetime import datetime

from django.utils import timezone

from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory

from . import models


class LegacyDefinitionTableFactory(DjangoModelFactory[models.LegacyDefinitionTable]):
    """DefinitionTable factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyDefinitionTable

    name = 'questionnaire'


class LegacyDictionaryFactory(DjangoModelFactory[models.LegacyDictionary]):
    """Dictionary factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyDictionary

    content = 'Edmonton Symptom Assessment Survey'
    content_id = Sequence(lambda number: number + 1)
    table = SubFactory(LegacyDefinitionTableFactory)
    language_id = 1
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    created_by = 'TestUser'
    updated_by = 'TestUser'


class LegacyPurposeFactory(DjangoModelFactory[models.LegacyPurpose]):
    """Purpose factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyPurpose

    title = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)


class LegacyRespondentFactory(DjangoModelFactory[models.LegacyRespondent]):
    """Respondent factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRespondent

    title = SubFactory(LegacyDictionaryFactory)
    description = SubFactory(LegacyDictionaryFactory)


class LegacyQuestionnaireFactory(DjangoModelFactory[models.LegacyQuestionnaire]):
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
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    created_by = 'Test User'
    updated_by = 'Test User'
    legacy_name = 'Test Questionnaire'


class LegacyQuestionnairePatientFactory(DjangoModelFactory[models.LegacyQuestionnairePatient]):
    """Patient factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestionnairePatient
        django_get_or_create = ('external_id',)

    external_id = 51
    hospital_id = -1
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    deleted_by = 'Test User'
    created_by = 'Test User'
    updated_by = 'Test User'


class LegacyAnswerQuestionnaireFactory(DjangoModelFactory[models.LegacyAnswerQuestionnaire]):
    """AnswerQuestionnaire factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerQuestionnaire

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    patient = SubFactory(LegacyQuestionnairePatientFactory)
    status = 0
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    deleted_by = 'Test User'
    created_by = 'Test User'
    updated_by = 'Test User'


class LegacyLanguageFactory(DjangoModelFactory[models.LegacyLanguage]):
    """Language factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyLanguage

    iso_lang = 'en'
    name = SubFactory(LegacyDictionaryFactory)
    deleted = False
    deleted_by = ''
    created_by = Faker('name')
    updated_by = Faker('name')


class LegacySectionFactory(DjangoModelFactory[models.LegacySection]):
    """Section factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacySection

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    title = SubFactory(LegacyDictionaryFactory)
    instruction = SubFactory(LegacyDictionaryFactory)
    order = Sequence(lambda number: number)
    deleted = False
    created_by = Faker('name')
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    updated_by = Faker('name')


class LegacyTypeFactory(DjangoModelFactory[models.LegacyType]):
    """Type factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyType

    description = SubFactory(LegacyDictionaryFactory)
    table = SubFactory(LegacyDefinitionTableFactory)
    sub_table = SubFactory(LegacyDefinitionTableFactory)
    template_table = SubFactory(LegacyDefinitionTableFactory)
    template_sub_table = SubFactory(LegacyDefinitionTableFactory)


class LegacyQuestionFactory(DjangoModelFactory[models.LegacyQuestion]):
    """Question factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestion
        django_get_or_create = ('display', 'definition', 'question', 'type')

    display = SubFactory(LegacyDictionaryFactory)
    definition = SubFactory(LegacyDictionaryFactory)
    question = Sequence(lambda number: number)
    type = SubFactory(LegacyTypeFactory)
    version = 1
    parent_id = -1
    private = False
    final = False
    optional_feedback = False
    deleted = False
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    created_by = Faker('name')
    updated_by = Faker('name')


class LegacyRadioButtonFactory(DjangoModelFactory[models.LegacyRadioButton]):
    """RadioButton factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRadioButton

    question = SubFactory(LegacyQuestionFactory)


class LegacyRadioButtonOptionFactory(DjangoModelFactory[models.LegacyRadioButtonOption]):
    """RadioButtonOption factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyRadioButtonOption

    parent_table = SubFactory(LegacyRadioButtonFactory)
    description = SubFactory(LegacyDictionaryFactory)
    order = Sequence(lambda number: number)


class LegacyCheckboxFactory(DjangoModelFactory[models.LegacyCheckbox]):
    """CheckBox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyCheckbox

    question = SubFactory(LegacyQuestionFactory)


class LegacyCheckboxOptionFactory(DjangoModelFactory[models.LegacyCheckboxOption]):
    """CheckBoxOption factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyCheckboxOption

    order = Faker('random_int')
    description = SubFactory(LegacyDictionaryFactory)
    parent_table = SubFactory(LegacyCheckboxFactory)


class LegacyLabelFactory(DjangoModelFactory[models.LegacyLabel]):
    """Label factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyLabel

    question = SubFactory(LegacyQuestionFactory)


class LegacyLabelOptionFactory(DjangoModelFactory[models.LegacyLabelOption]):
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


class LegacyQuestionSectionFactory(DjangoModelFactory[models.LegacyQuestionSection]):
    """Type factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyQuestionSection

    question = SubFactory(LegacyQuestionFactory)
    section = SubFactory(LegacySectionFactory)
    order = Sequence(lambda number: number)
    orientation = 0
    optional = False


class LegacyAnswerSectionFactory(DjangoModelFactory[models.LegacyAnswerSection]):
    """AnswerSection factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerSection

    answer_questionnaire = SubFactory(LegacyAnswerQuestionnaireFactory)
    section = SubFactory(LegacySectionFactory)


class LegacyAnswerFactory(DjangoModelFactory[models.LegacyAnswer]):
    """Answer factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswer

    questionnaire = SubFactory(LegacyQuestionnaireFactory)
    section = SubFactory(LegacySectionFactory)
    question = SubFactory(LegacyQuestionFactory)
    type = SubFactory(LegacyTypeFactory)
    answer_section = SubFactory(LegacyAnswerSectionFactory)
    language = SubFactory(LegacyLanguageFactory)
    patient = SubFactory(LegacyQuestionnairePatientFactory)
    answered = Faker('boolean')
    skipped = Faker('boolean')
    deleted = Faker('boolean')
    deleted_by = Faker('word')
    creation_date = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    created_by = Faker('word')
    updated_by = Faker('word')


class LegacyAnswerSliderFactory(DjangoModelFactory[models.LegacyAnswerSlider]):
    """AnswerSlider factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerSlider

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('pyfloat', positive=True, min_value=1, max_value=10)


class LegacyAnswerTextBoxFactory(DjangoModelFactory[models.LegacyAnswerTextBox]):
    """AnswerTextBox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerTextBox

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('text', max_nb_chars=200)


class LegacyAnswerTimeFactory(DjangoModelFactory[models.LegacyAnswerTime]):
    """AnswerTime factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerTime

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('time')


class LegacyAnswerLabelFactory(DjangoModelFactory[models.LegacyAnswerLabel]):
    """AnswerLabel factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerLabel

    answer = SubFactory(LegacyAnswerFactory)
    selected = 1
    pos_x = Faker('pyint')
    pos_y = Faker('pyint')
    intensity = Faker('pyint')
    value = Faker('pyint')


class LegacyAnswerRadioButtonFactory(DjangoModelFactory[models.LegacyAnswerRadioButton]):
    """AnswerRadioButton factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerRadioButton

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('random_int')


class LegacyAnswerCheckboxFactory(DjangoModelFactory[models.LegacyAnswerCheckbox]):
    """AnswerCheckbox factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerCheckbox

    answer = SubFactory(LegacyAnswerFactory)
    value = Faker('random_int')


class LegacyAnswerDateFactory(DjangoModelFactory[models.LegacyAnswerDate]):
    """AnswerDate factory from the legacy questionnaire database."""

    class Meta:
        model = models.LegacyAnswerDate

    answer = SubFactory(LegacyAnswerFactory)
    value = datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
