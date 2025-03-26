import pytest

from .. import factories

pytestmark = pytest.mark.django_db()


def test_general_test_factory() -> None:
    """Ensure the `GeneralTest` factory creates a valid model."""
    test = factories.GeneralTestFactory()
    test.full_clean()


def test_observation_factory() -> None:
    """Ensure the `Observation` factory creates a valid model."""
    observation = factories.ObservationFactory()
    observation.full_clean()


def test_note_factory() -> None:
    """Ensure the `Note` factory creates a valid model."""
    note = factories.NoteFactory()
    note.full_clean()


def test_multi_obx_test() -> None:
    """Ensure multiple observation and note instances can be assigned to one GeneralTest."""
    test = factories.GeneralTestFactory()
    obx1 = factories.ObservationFactory(general_test=test)
    obx2 = factories.ObservationFactory(general_test=test)
    obx3 = factories.ObservationFactory(general_test=test)
    obx4 = factories.ObservationFactory(general_test=test)
    nte1 = factories.NoteFactory(general_test=test)
    nte2 = factories.NoteFactory(general_test=test)

    components = [obx1, obx2, obx3, obx4, nte1, nte2]
    for component in components:
        assert component.general_test.type == test.type  # type: ignore[attr-defined]
        component.full_clean()  # type: ignore[attr-defined]
