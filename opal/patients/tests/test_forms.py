import pytest

from ..forms import RelationshipPendingAccessForm
from ..models import Relationship

pytestmark = pytest.mark.django_db


def test_relationshippending_form_is_valid(relationshippending_form: RelationshipPendingAccessForm) -> None:
    """Ensure that the `RelationshipPendingAccess` form is valid."""
    assert relationshippending_form.is_valid()


def test_relationshippending_missing_startdate(
    incomplete_relationshippending_form: RelationshipPendingAccessForm,
) -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    assert not incomplete_relationshippending_form.is_valid()


def test_relationshippending_update(relationshippending_form: RelationshipPendingAccessForm) -> None:
    """Ensure that a valid `RelationshipPendingAccess` form can be saved."""
    relationshippending_form.save()
    assert Relationship.objects.all()[0].start_date == relationshippending_form.data['start_date']


def test_relationshippending_update_fail(
    incomplete_relationshippending_form: RelationshipPendingAccessForm,
) -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    message = 'This field is required.'

    assert not incomplete_relationshippending_form.is_valid()
    assert incomplete_relationshippending_form.errors['start_date'][0] == message


def test_relationshippending_form_date_validated(
    wrong_date_relationshippending_form: RelationshipPendingAccessForm,
) -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for startdate>enddate."""
    message = 'Start date should be earlier than end date.'

    assert not wrong_date_relationshippending_form.is_valid()
    assert wrong_date_relationshippending_form.errors['start_date'][0] == message


def test_relationshippending_status_reason(
    empty_reason_denied_relationshippending_form: RelationshipPendingAccessForm,
) -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for reason is not empty when status is denied."""
    message = 'Reason is mandatory when status is denied or revoked.'

    assert not empty_reason_denied_relationshippending_form.is_valid()
    assert empty_reason_denied_relationshippending_form.errors['reason'][0] == message
