import csv
from pathlib import Path

import pytest

from opal.services.data_processing.deidentification import OpenScienceIdentity, PatientData

pytestmark = pytest.mark.django_db(databases=['default'])


FIXTURES_DIR = Path(__file__).resolve().parent.joinpath('fixtures')

# # Define the path to the CSV file
# csv_file_path = os.path.join(
#     Path(__file__).resolve(strict=True).parents[3] / 'tests' / 'fixtures',
#     'attributes_expected_signatures.csv',
# )

# Reading the CSV file and creating a list of test cases
test_cases = []
with FIXTURES_DIR.joinpath('attributes_expected_signatures.csv').open() as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        attributes = {
            'gender': row[0],
            'first_name': row[1],
            'middle_name': row[2],
            'last_name': row[3],
            'date_of_birth': row[4],
            'city_of_birth': row[5],
        }
        expected_signature = row[6]
        test_cases.append((attributes, expected_signature))


class TestOpenScienceIdentity:
    """Tests for the OpenScienceIdentity a.k.a GUID algorithm."""

    @pytest.mark.parametrize(('attributes', 'expected_signature'), test_cases)
    def test_signature_generation(self, attributes: dict[str, str], expected_signature: str) -> None:  # noqa: WPS442
        """Test the successful generation of signatures/guids for patients."""
        identity = OpenScienceIdentity(PatientData(**attributes))
        if expected_signature == 'invalid':
            with pytest.raises(ValueError, match='Invalid identity components'):
                identity.to_signature()
        else:
            generated_signature = identity.to_signature()
            assert generated_signature == expected_signature

    def test_empty_attributes(self) -> None:
        """Test the handling of empty attributes."""
        empty_attributes = {
            'gender': '',
            'first_name': '',
            'middle_name': '',
            'last_name': '',
            'date_of_birth': '',
            'city_of_birth': '',
        }
        with pytest.raises(ValueError, match='Invalid identity components'):
            OpenScienceIdentity(PatientData(**empty_attributes)).to_signature()

    def test_none_attribute_components(self) -> None:
        """Test the handling of None attribute components."""
        none_attributes_components = {
            'gender': None,
            'first_name': None,
            'middle_name': None,
            'last_name': None,
            'date_of_birth': None,
            'city_of_birth': None,
        }
        with pytest.raises(ValueError, match='Invalid identity components'):
            OpenScienceIdentity(PatientData(**none_attributes_components)).to_signature()
