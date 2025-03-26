"""This module is used to provide configuration, fixtures, and plugins for pytest within patients app."""
import datetime

from django.forms import model_to_dict

import pytest

from . import factories
from .forms import RelationshipPendingAccessForm
from .models import Relationship, RelationshipStatus


@pytest.fixture(name='relationship')
def relationship() -> Relationship:
    """Fixture providing an instance of `Relationship` model.

    Returns:
        an instance of `Relationship`
    """
    return factories.Relationship()


@pytest.fixture()
def relationshippending_form() -> RelationshipPendingAccessForm:
    """Fixture providing data for the `RelationshipPendingAccessForm`.

    Returns:
        RelationshipPendingAccessForm object
    """
    relationship_info = factories.Relationship.create()
    form_data = model_to_dict(relationship_info)

    return RelationshipPendingAccessForm(
        data=form_data,
        instance=relationship_info,
    )


@pytest.fixture()
def incomplete_relationshippending_form() -> RelationshipPendingAccessForm:
    """Fixture providing incomplete data for the `RelationshipPendingAccessForm`.

    Returns:
        RelationshipPendingAccessForm object
    """
    relationship_info = factories.Relationship.build()
    form_data = model_to_dict(relationship_info, exclude=[
        'start_date',
        'end_date',
    ])

    return RelationshipPendingAccessForm(
        data=form_data,
        instance=relationship_info,
    )


@pytest.fixture()
def wrong_date_relationshippending_form() -> RelationshipPendingAccessForm:
    """Fixture providing wrong date for the `RelationshipPendingAccessForm`.

    Returns:
        RelationshipPendingAccessForm object
    """
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(),
        caregiver=factories.CaregiverProfile(),
        type=factories.RelationshipType(),
        start_date=datetime.date(2022, 6, 1),  # noqa: WPS432
        end_date=datetime.date(2022, 5, 1),  # noqa: WPS432
    )
    form_data = model_to_dict(relationship_info)

    return RelationshipPendingAccessForm(
        data=form_data,
        instance=relationship_info,
    )


@pytest.fixture()
def empty_reason_denied_relationshippending_form() -> RelationshipPendingAccessForm:
    """Fixture providing denied status with empty reason for the `RelationshipPendingAccessForm`.

    Returns:
        RelationshipPendingAccessForm object
    """
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(),
        caregiver=factories.CaregiverProfile(),
        type=factories.RelationshipType(),
        status=RelationshipStatus.DENIED,
        start_date=datetime.date(2022, 5, 1),  # noqa: WPS432
        end_date=datetime.date(2022, 6, 1),  # noqa: WPS432
        reason='',
    )
    form_data = model_to_dict(relationship_info)

    return RelationshipPendingAccessForm(
        data=form_data,
        instance=relationship_info,
    )
