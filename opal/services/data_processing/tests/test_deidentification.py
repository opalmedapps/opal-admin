import csv
from pathlib import Path

import pytest

from opal.services.data_processing.deidentification import OpenScienceIdentity, PatientData
from opal.patients.models import SexType

pytestmark = pytest.mark.django_db(databases=['default'])


FIXTURES_DIR = Path(__file__).resolve().parent.joinpath('fixtures')

# Reading the CSV file and creating a list of test cases
test_cases = []
with FIXTURES_DIR.joinpath('attributes_expected_signatures.csv').open() as csv_file:
    reader = csv.reader(csv_file)
    # Mapping gender string to SexType enum
    sex_type_mapping = {
        'male': SexType.MALE,
        'masculin': SexType.MALE,
        'female': SexType.FEMALE,
        'féminin': SexType.FEMALE,
        'other': SexType.OTHER,
        'unknown': SexType.UNKNOWN,
    }

    for row in reader:
        gender_str = row[0].strip().lower()
        gender = sex_type_mapping.get(gender_str, None)

        attributes = {
            'first_name': row[1],
            'middle_name': row[2],
            'last_name': row[3],
            'date_of_birth': row[4],
            'city_of_birth': row[5],
        }
        expected_signature = row[6]
        test_cases.append((gender, attributes, expected_signature))


class TestOpenScienceIdentity:
    """Tests for the OpenScienceIdentity a.k.a GUID algorithm."""

    @pytest.mark.parametrize(('gender', 'attributes', 'expected_signature'), test_cases)
    def test_signature_generation(self, gender: SexType, attributes: dict[str, str], expected_signature: str) -> None:  # noqa: WPS442, E501
        """Test the successful generation of signatures/guids for patients."""
        identity = OpenScienceIdentity(PatientData(gender=gender, **attributes))
        if expected_signature == 'invalid':
            with pytest.raises(ValueError, match='Invalid identity components'):
                identity.to_signature()
        else:
            generated_signature = identity.to_signature()
            assert generated_signature == expected_signature

    def test_empty_attributes(self) -> None:
        """Test the handling of empty attributes."""
        empty_gender = SexType.UNKNOWN
        empty_attributes = {
            'first_name': '',
            'middle_name': '',
            'last_name': '',
            'date_of_birth': '',
            'city_of_birth': '',
        }
        with pytest.raises(ValueError, match='Invalid identity components'):
            OpenScienceIdentity(PatientData(gender=empty_gender, **empty_attributes)).to_signature()
