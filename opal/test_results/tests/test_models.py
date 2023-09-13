from datetime import datetime

from django.utils import timezone

import pytest

from .. import factories, models

pytestmark = pytest.mark.django_db()


def test_general_test_factory() -> None:
    """Ensure the `GeneralTest` factory creates a valid model."""
    test = factories.GeneralTest()
    test.full_clean()


def test_observation_factory() -> None:
    """Ensure the `Observation` factory creates a valid model."""
    observation = factories.Observation()
    observation.full_clean()


def test_note_factory() -> None:
    """Ensure the `Note` factory creates a valid model."""
    note = factories.Note()
    note.full_clean()


def test_multi_observations_test() -> None:
    """Ensure multiple observation and note instances can be assigned to one GeneralTest."""
    test = factories.GeneralTest()
    observation1 = factories.Observation(general_test=test)
    observation2 = factories.Observation(general_test=test)
    observation3 = factories.Observation(general_test=test)
    observation4 = factories.Observation(general_test=test)
    note1 = factories.Note(general_test=test)
    note2 = factories.Note(general_test=test)

    components = [observation1, observation2, observation3, observation4, note1, note2]
    for component in components:
        assert component.general_test.type == test.type  # type: ignore[attr-defined]
        component.full_clean()  # type: ignore[attr-defined]


def test_general_test_str() -> None:
    """Ensure the __str__ method for GeneralTest works properly."""
    general_test = factories.GeneralTest(
        type=models.TestType.PATHOLOGY,
        collected_at=timezone.make_aware(datetime.today()),
    )
    assert str(general_test) == f'{general_test.patient} Pathology Test instance [{general_test.collected_at}]'


def test_observation_str() -> None:
    """Ensure the __str__ method for Obseration works properly."""
    general_test = factories.GeneralTest(
        type=models.TestType.PATHOLOGY,
    )
    observation = factories.Observation(
        general_test=general_test,
        value='Left breast mass',
        value_abnormal=models.AbnormalFlag.NORMAL,
    )
    assert str(observation) == f'SPSPECI : Left breast mass  [{models.AbnormalFlag.NORMAL}]'


def test_note_str() -> None:
    """Ensure the __str__ method for Note works properly."""
    general_test = factories.GeneralTest(
        type=models.TestType.PATHOLOGY,
        collected_at=timezone.make_aware(datetime.today()),
    )
    note = factories.Note(
        general_test=general_test,
        note_text='Generic pathologist note',
    )
    assert str(note) == '{generaltest} | {note}'.format(
        generaltest=str(general_test),
        note='Generic pathologist note',
    )
