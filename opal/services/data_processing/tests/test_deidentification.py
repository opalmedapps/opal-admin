import csv
from pathlib import Path

import pytest

from opal.services.data_processing.deidentification import OpenScienceIdentity, PatientData

pytestmark = pytest.mark.django_db(databases=['default'])


FIXTURES_DIR = Path(__file__).resolve().parent.joinpath('fixtures')

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
