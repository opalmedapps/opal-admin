from collections import defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest

from opal.core.drf_parsers import hl7_parser

pytestmark = pytest.mark.django_db(databases=['default'])
FIXTURES_DIR = Path(__file__).resolve().parent.joinpath('fixtures')

@pytest.fixture
def parser():
    """Fixture for creating an HL7Parser instance."""
    return hl7_parser.HL7Parser()


class TestHL7Parser:
    """Class wrapper for HL7Parser tests."""

    # parse repeatable segments into a list
    # apply parser context to limit parsed segments
    # handled malformed hl7 gracefully
    # removes invalid sites
    # removes invalid breaking characters

    def _assert_segment_data(self, segment_data, expected_values, segment_name):
        """Utility method to assert that the segment data matches the expected values."""
        # Assert correct values for each key in the segment, which also implicitly checks for their presence
        for key, expected_value in expected_values.items():
            actual_value = segment_data.get(key, None)
            assert str(actual_value) == expected_value, f"Expected {segment_name} segment's {key} to be {expected_value}, got {actual_value}"

        # Check for any unexpected keys in the segment data
        unexpected_keys = set(segment_data.keys()) - set(expected_values.keys())
        assert not unexpected_keys, f"Unexpected keys present in {segment_name} segment: {unexpected_keys}"


    def _load_hl7_fixture(self, filename):
        """Utility function to load an HL7 fixture file into a bytestream."""
        with (FIXTURES_DIR / filename).open('r') as file:
            return StringIO(file.read())

    def test_parse_pid_segment(self, parser):
        """Test parsing a PID segment."""
        stream = self._load_hl7_fixture('marge_PID.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'PID' in parsed_data, "PID segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        expected_values = {
            'first_name': 'MARGE',
            'last_name': 'SIMPSON',
            'date_of_birth': '1987-10-01',
            'sex': 'F',
            'ramq': 'SIMM86600199',
            'address_street': '742 EVERGREEN TERRACE',
            'address_city': 'SPRINGFIELD',
            'address_province': '',
            'address_postal_code': '',
            'address_country': 'USA',
            'phone_number': '(555)123-4567',
            'primary_language': 'English',
            'marital_status': '',
            'mrn_sites': '[]',
        }
        # Use the utility method to assert the PID segment data
        self._assert_segment_data(parsed_data['PID'], expected_values, "PID")

    def test_parse_pv1_segment(self, parser):
        """Test parsing a PV1 segment."""
        stream = self._load_hl7_fixture('marge_PV1.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'PV1' in parsed_data, "PV1 segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        pv1_data = parsed_data['PV1'][0]
        expected_values = {
            'location_poc': 'HRZL',
            'location_room': '43',
            'location_bed': 'A',
            'location_facility': 'RVH',
            'visit_number': '000002050173412'
        }

        # Use the utility method to assert the segment data
        self._assert_segment_data(pv1_data, expected_values, "PV1")


    def test_parse_orc_segment(self, parser):
        """Test parsing a ORC segment."""
        stream = self._load_hl7_fixture('marge_ORC.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'ORC' in parsed_data, "ORC segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        orc_data = parsed_data['ORC'][0]
        expected_values = {
            'order_control': 'XX',
            'filler_order_number': '25008915',
            'order_status': 'SC',
            'order_quantity': '0.17',
            'order_quantity_unit': '',
            'order_interval_pattern': 'Q24',
            'order_interval_duration': '1000',
            'order_duration': 'INDEF',
            'order_start_datetime': '2023-12-06 10:00:00-05:00',
            'order_end_datetime': '2024-12-05 18:59:00-05:00',
            'order_priority': 'R',
            'entered_at': '2023-12-06 13:16:10-05:00',
            'entered_by_id': 'MDUCEPPE',
            'entered_by_family_name': 'Duceppe',
            'entered_by_given_name': 'Marc-Alexandre',
            'verified_by_id': 'MDUCEPPE',
            'verified_by_family_name': 'Duceppe',
            'verified_by_given_name': 'Marc-Alexandre',
            'ordered_by_id': '100000',
            'order_by_family_name': 'Emergency',
            'order_by_given_name': 'Dr.',
            'effective_at': '2023-12-06 10:00:00-05:00',
        }
        # Use the utility method to assert the segment data
        self._assert_segment_data(orc_data, expected_values, "ORC")


    def test_parse_rxe_segment(self, parser):
        """Test parsing a RXE segment."""
        stream = self._load_hl7_fixture('marge_RXE.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'RXE' in parsed_data, "RXE segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        rxe_data = parsed_data['RXE'][0]
        expected_values = {
            'pharmacy_quantity': '0.17',
            'pharmacy_quantity_unit': 'Q24&1000',
            'pharmacy_interval_pattern': 'Q24',
            'pharmacy_interval_duration': '1000',
            'pharmacy_duration': 'INDEF',
            'pharmacy_start_datetime': '2023-12-06 10:00:00-05:00',
            'pharmacy_end_datetime': '2024-12-05 18:59:00-05:00',
            'pharmacy_priority': 'R',
            'give_identifier': 'ENOXAREDES100I3',
            'give_text': 'ENOXAPARIN (REDESCA) IJ',
            'give_coding_system': 'RXTFC',
            'give_alt_identifier': '20:12.04',
            'give_alt_text': 'ANTICOAGULANTS',
            'give_alt_coding_system': 'AHFS',
            'give_amount_maximum': '50',
            'give_amount_minimum': '',
            'give_units': 'MG',
            'give_dosage_identifier': 'INJVIAL',
            'give_dosage_text': 'VIAL INJ',
            'give_dosage_coding_system': 'RxTFC',
            'provider_administration_instruction': '50 mg = 0.5 mL SC Q24H \nBLEEDING RISK- ANTICOAGULANT\n* HIGH ALERT  *',
            'dispense_amount': '50',
            'dispense_units': 'MG',
            'refills': '0.00',
            'refills_remaining': '0.000',
            'prescription_number': '21',
            'refills_dispensed': '0',
            'give_per_time': 'H0',
            'give_rate_amount': '0',
            'give_rate_identifier': 'mL/hr',
            'give_rate_units': 'mL/hr'
        }

        # Use the utility method to assert the segment data
        self._assert_segment_data(rxe_data, expected_values, "RXE")


    def test_parse_rxr_segment(self, parser):
        """Test parsing a RXR segment."""
        stream = self._load_hl7_fixture('marge_RXR.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'RXR' in parsed_data, "RXR segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        rxr_data = parsed_data['RXR'][0]
        expected_values = {
            'route_identifier': 'SCMED',
            'route_text': 'SC Injection (Med Order)',
            'route_coding_system': 'RxTFC',
            'route_alt_identifier': '',
            'route_alt_text': '',
            'route_alt_coding_system': '',
            'route_site': '',
            'route_administration_device': '',
            'route_administration_identifier': 'IJ',
            'route_administration_text': 'Inj Syringe',
            'route_administration_coding_system': 'RxTFC',
            'route_administration_alt_identifier': '',
            'route_administration_alt_text': '',
            'route_administration_alt_coding_system': ''
        }
        # Use the utility method to assert the segment data
        self._assert_segment_data(rxr_data, expected_values, "RXR")


    def test_parse_rxc_segment(self, parser):
        """Test parsing a RXC segment."""
        stream = self._load_hl7_fixture('marge_RXC.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'RXC' in parsed_data, "RXC segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        rxc_data = parsed_data['RXC'][0]
        expected_values = {
            'component_type': 'A',
            'component_identifier': 'ENOXAREDES100I3',
            'component_text': 'ENOXAPARIN (REDESCA)',
            'component_coding_system': 'RXTFC',
            'component_alt_identifier': '20:12.04',
            'component_alt_text': 'ANTICOAGULANTS',
            'component_alt_coding_system': 'AHFS',
            'component_amount': '50',
            'component_units': 'MG'
        }
        # Use the utility method to assert the segment data
        self._assert_segment_data(rxc_data, expected_values, "RXC")

    def test_parse_nte_segment(self, parser):
        """Test parsing a NTE segment."""
        stream = self._load_hl7_fixture('marge_NTE.hl7v2')
        parsed_data = parser.parse(stream)
        assert 'NTE' in parsed_data, "NTE segment should be present in parsed data"
        assert isinstance(parsed_data, defaultdict), "Data should be a defaultdict"
        nte_data = parsed_data['NTE'][0]
        expected_values = {
            'note_id': '2',
            'note_comment_id': 'L',
            'note_comment_text': 'STD'
        }
        # Use the utility method to assert the segment data
        self._assert_segment_data(nte_data, expected_values, "NTE")
