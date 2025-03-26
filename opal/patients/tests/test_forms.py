from typing import Tuple

import pytest

from opal.hospital_settings import factories

from ..forms import ConfirmPatientForm, SearchForm, SelectSiteForm

pytestmark = pytest.mark.django_db


def test_site_selection_exist() -> None:
    """Ensure that the site seletion is valid."""
    site = factories.Site(name='Montreal General Hospital', code='MGH')
    form_data = {
        'sites': site,
    }

    form = SelectSiteForm(data=form_data)

    assert form.is_valid()


def test_site_selection_not_exist() -> None:
    """Ensure that the empty site seletion is not valid."""
    form_data = {
        'sites': '',
    }

    form = SelectSiteForm(data=form_data)

    assert not form.is_valid()


# tuple with valid medical card type and medical number
# will update the test data once the validator is done in another ticket
test_valid_medical_card_type_and_number: list[Tuple] = [
    ('mrn', 'MRNT99996666'),
    ('ramq', 'RAMQ99996666'),
    ('mrn', 'MRNT00001111'),
]


@pytest.mark.parametrize(('card_type', 'card_number'), test_valid_medical_card_type_and_number)
def test_search_form_valid(
    card_type: str,
    card_number: str,
) -> None:
    """Ensure that the search form is valid."""
    form_data = {
        'medical_card': card_type,
        'medical_number': card_number,
    }
    form = SearchForm(data=form_data)
    assert form.is_valid()


# tuple with invalid medical card type and medical number
test_invalid_medical_card_type_and_number: list[Tuple] = [
    ('ramq', 'ramq99996666'),
]


@pytest.mark.parametrize(('card_type', 'card_number'), test_invalid_medical_card_type_and_number)
def test_search_form_invalid_ramq_field(
    card_type: str,
    card_number: str,
) -> None:
    """Ensure that the search form is valid."""
    form_data = {
        'medical_card': card_type,
        'medical_number': card_number,
    }
    form = SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits']


def test_is_correct_checked() -> None:
    """Ensure that the 'Correct?' checkbox is checked."""
    form_data = {
        'is_correct': True,
    }

    form = ConfirmPatientForm(data=form_data)

    assert form.is_valid()


def test_is_correct_not_checked() -> None:
    """Ensure that the 'Correct?' checkbox is not checked."""
    form_data = {
        'is_correct': False,
    }

    form = ConfirmPatientForm(data=form_data)

    assert not form.is_valid()
