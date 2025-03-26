from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from .. import factories, models

pytestmark = pytest.mark.django_db()


def test_general_test_factory() -> None:
    """Ensure the `GeneralTest` factory creates a valid model."""
    test = factories.GeneralTest()
    test.full_clean()


def test_pathology_observation_factory() -> None:
    """Ensure the `PathologyObservation` factory creates a valid model."""
    pathology_observation = factories.PathologyObservationFactory()
    pathology_observation.full_clean()


def test_lab_observation_factory() -> None:
    """Ensure the `LabObservation` factory creates a valid model."""
    lab_observation = factories.LabObservationFactory()
    lab_observation.full_clean()


def test_note_factory() -> None:
    """Ensure the `Note` factory creates a valid model."""
    note = factories.Note()
    note.full_clean()


def test_multi_observations_test() -> None:
    """Ensure multiple observation and note instances can be assigned to one GeneralTest."""
    test = factories.GeneralTest(type=models.TestType.PATHOLOGY)
    observation1 = factories.PathologyObservationFactory(general_test=test)
    observation2 = factories.PathologyObservationFactory(general_test=test)
    observation3 = factories.PathologyObservationFactory(general_test=test)
    observation4 = factories.PathologyObservationFactory(general_test=test)
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


def test_pathology_observation_str() -> None:
    """Ensure the __str__ method for PathologyObseration works properly."""
    general_test = factories.GeneralTest(
        type=models.TestType.PATHOLOGY,
    )
    observation = factories.PathologyObservationFactory(
        general_test=general_test,
        observed_at=timezone.make_aware(datetime.today()),
    )
    assert str(observation) == f'SPSPECI: {observation.observed_at}'


def test_lab_observation_str() -> None:
    """Ensure the __str__ method for LabObseration works properly."""
    general_test = factories.GeneralTest(
        type=models.TestType.LAB,
    )
    observation = factories.LabObservationFactory(
        general_test=general_test,
        value=3.0,
        value_units='10^9/L',
        value_abnormal=models.AbnormalFlag.HIGH,
    )
    assert str(observation) == 'WBC: 3.0 10^9/L [H]'


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


def test_save_pathology_observation_correct_type() -> None:
    """Test save behaviour of PathologyObservations for correct type."""
    pathology_test = factories.GeneralTest(type=models.TestType.PATHOLOGY)
    observation = factories.PathologyObservationFactory(general_test=pathology_test)
    # This should not raise any exceptions
    observation.full_clean()


def test_save_pathology_observation_incorrect_type() -> None:
    """Test save behaviour of PathologyObservations for incorrect type."""
    lab_test = factories.GeneralTest(type=models.TestType.LAB)
    pathology_observation = factories.PathologyObservationFactory(general_test=lab_test)

    with pytest.raises(ValidationError) as exc_info:
        pathology_observation.full_clean()

    # Check if desired error message is in the list of error messages
    assert 'PathologyObservations can only be linked to GeneralTest of type PATHOLOGY.' in exc_info.value.messages


def test_save_lab_observation_correct_type() -> None:
    """Test save behaviour of LabObservations for correct type."""
    lab_test = factories.GeneralTest(type=models.TestType.LAB)
    observation = factories.LabObservationFactory(general_test=lab_test)
    # This should not raise any exceptions
    observation.full_clean()


def test_save_lab_observation_incorrect_type() -> None:
    """Test save behaviour of LabObservations for incorrect type."""
    pathology_test = factories.GeneralTest(type=models.TestType.PATHOLOGY)
    lab_observation = factories.LabObservationFactory(general_test=pathology_test)
    with pytest.raises(ValidationError) as exc_info:
        lab_observation.full_clean()

    # Check if desired error message is in the list of error messages
    assert 'LabObservations can only be linked to GeneralTest of type LAB.' in exc_info.value.messages


def test_general_test_observations_reverse_relationship() -> None:
    """Test that the observations property correctly returns a GeneralTest's observation instances."""
    # Create a GeneralTest instance of type PATHOLOGY
    pathology_test = factories.GeneralTest(type=models.TestType.PATHOLOGY)

    # Create a related PathologyObservation instance
    factories.PathologyObservationFactory(general_test=pathology_test)

    # Check that the observations property returns PathologyObservation
    assert pathology_test.observations.count() == 1
    for path_observation in pathology_test.observations:
        assert isinstance(path_observation, models.PathologyObservation)

    # Create a GeneralTest instance of type LAB
    lab_test = factories.GeneralTest(type=models.TestType.LAB)

    # Create a related LabObservation instance
    factories.LabObservationFactory(general_test=lab_test)

    # Check that the observations property returns LabObservation
    assert lab_test.observations.count() == 1
    for lab_observation in lab_test.observations:
        assert isinstance(lab_observation, models.LabObservation)

    assert models.GeneralTest.objects.count() == 2
