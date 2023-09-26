import pytest

from opal.services.data_processing.deidentification import OpenScienceIdentity

pytestmark = pytest.mark.django_db(databases=['default'])


def test_signature_generation() -> None:
    """Test the successful generation of signatures/guids for patients."""
    attributes = {
        'gender': 'Male',
        'first_name': 'Pierre',
        'middle_name': 'Tiberius',
        'last_name': 'Rioux',
        'date_of_birth': '1901-01-02',
        'city_of_birth': 'Longueuil',
    }
    expected_signature = '99e391f4efeb041a03f310e159ffaa36583d9ee91691333def6b387048868343'

    identity = OpenScienceIdentity(attributes)
    generated_signature = identity.to_signature()
    assert generated_signature == expected_signature
