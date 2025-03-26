import datetime

from django.forms import model_to_dict

import pytest

from .. import factories
from ..forms import RelationshipPendingAccessForm
from ..models import Relationship, RelationshipStatus

pytestmark = pytest.mark.django_db


def test_relationshippending_form_is_valid() -> None:
    """Ensure that the `RelationshipPendingAccess` form is valid."""
    relationship_info = factories.Relationship.create()
    form_data = model_to_dict(relationship_info)

    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)

    assert relationshippending_form.is_valid()


def test_relationshippending_missing_startdate() -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    relationship_info = factories.Relationship.build()
    form_data = model_to_dict(relationship_info, exclude=[
        'start_date',
        'end_date',
    ])

    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)
    assert not relationshippending_form.is_valid()


def test_relationshippending_update() -> None:
    """Ensure that a valid `RelationshipPendingAccess` form can be saved."""
    relationship_info = factories.Relationship.create()
    form_data = model_to_dict(relationship_info)

    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)
    relationshippending_form.save()

    assert Relationship.objects.all()[0].start_date == relationshippending_form.data['start_date']


def test_relationshippending_update_fail() -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    relationship_info = factories.Relationship.build()
    form_data = model_to_dict(relationship_info, exclude=[
        'start_date',
        'end_date',
    ])

    message = 'This field is required.'
    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)

    assert not relationshippending_form.is_valid()
    assert relationshippending_form.errors['start_date'][0] == message


def test_relationshippending_form_date_validated() -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for startdate>enddate."""
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(),
        caregiver=factories.CaregiverProfile(),
        type=factories.RelationshipType(),
        start_date=datetime.date(2022, 6, 1),  # noqa: WPS432
        end_date=datetime.date(2022, 5, 1),  # noqa: WPS432
    )
    form_data = model_to_dict(relationship_info)

    message = 'Start date should be earlier than end date.'
    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)

    assert not relationshippending_form.is_valid()
    assert relationshippending_form.errors['start_date'][0] == message


def test_relationshippending_status_reason() -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for reason is not empty when status is denied."""
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

    message = 'Reason is mandatory when status is denied or revoked.'
    relationshippending_form = RelationshipPendingAccessForm(data=form_data, instance=relationship_info)

    assert not relationshippending_form.is_valid()
    assert relationshippending_form.errors['reason'][0] == message
