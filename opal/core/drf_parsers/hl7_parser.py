"""Module which provides HL7-parsing into JSON data for any generic HL7 segment-structured message."""
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Mapping, TypedDict
from django.utils import timezone
from hl7apy.core import Segment
from hl7apy.parser import parse_message
from rest_framework.parsers import BaseParser


class HL7Parser(BaseParser):
    """Parse HL7-v2 messages and return TypedDict data."""

    media_type = 'application/hl7-v2+er7'

    def __init__(self):
        """Initialize the segment parsing functions."""
        self.segment_parsers: dict[str, function] = {
            'PID': self._parse_pid_segment,
            'PV1': self._parse_pv1_segment,
            'ORC': self._parse_orc_segment,
            'RXE': self._parse_rxe_segment,
            'RXC': self._parse_rxc_segment,
            'RXR': self._parse_rxr_segment,
            'NTE': self._parse_nte_segment,
        }
        # Initialize a dictionary to hold the parsed data, one PID segment only, and all other segments as lists.
        self.message_dict: TypedDict = {name: {} if name =='PID' else [] for name in self.segment_parsers.keys()}

    def parse(
        self,
        stream: IO,
        media_type: str | None = 'application/hl7-v2+er7',
        parser_context: Mapping[str, Any] | None = None,
    ) -> TypedDict:
        """Parse the incoming bytestream as an HL7v2 message and return JSON.

        Args:
            stream: Incoming byte stream of request data
            media_type: Acceptable data/media type
            parser_context: Additional request metadata to specify parsing functionality

        Returns:
            TypedDict object containing the parsed HL7v2 message
        """
        # Read the incoming stream into a string
        raw_data = stream.read()
        # Normalize line endings to CR
        hl7_message = raw_data.replace('\r\n', '\r').replace('\n', '\r')
        # Use hl7apy to parse the message, find_groups=False disables the higher level segment grouping
        # For example, find_groups would typically bundles PID and PV1 into their own 'RDE_O01_PATIENT' grouping)
        for segment in parse_message(hl7_message, find_groups=False).children:
            # TODO: Do we want to consider using the parser_context to determine which segments to parse?
            # This could reduce parse time since currently this class will parse every segment it finds which has a parse method
            # If instead we had the APIView pass a context (a.k.a which HL7 segments it needs) we could skip parsing un-wanted segments
            # This would become more useful/time-saving as we define additional parse methods for new HL7 segment types (e.g OBX for lab data)
            segment_name = segment.name
            # Find the appropriate parsing function based on the segment name
            parse_function = self.segment_parsers.get(segment_name)

            # If a parsing function is defined, use it to parse the segment
            if parse_function and segment_name=='PID':
                # Only 1 PID segment is ever expected
                self.message_dict[segment_name] = parse_function(segment)
            elif parse_function:
                # Other segment types can have multiple
                self.message_dict[segment_name].append(parse_function(segment))

        return self.message_dict

    def _parse_pid_segment(self, segment: Segment) -> dict:
        """Extract patient data from an HL7v2 PID segment.

        Use the HL7 documentation to know which fields contain the correct data:
        https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/PID

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'first_name': segment.pid_5.pid_5_2.to_er7(),
            'last_name': segment.pid_5.pid_5_1.to_er7(),
            'date_of_birth': datetime.strptime(segment.pid_7.to_er7(), '%Y%m%d').date(),
            'sex': segment.pid_8.to_er7(),
            'ramq': segment.pid_2.pid_2_1.to_er7(),
            # TODO: Kill the mrn_sites which aren't in the 'approved/existing site list'
            'mrn_sites': [(mrn_site.pid_3_1.to_er7(), mrn_site.pid_3_4.to_er7()) for mrn_site in segment.pid_3],
            'address_street': segment.pid_11.pid_11_1.to_er7(),
            'address_city': segment.pid_11.pid_11_3.to_er7(),
            'address_province': segment.pid_11.pid_11_4.to_er7(),
            'address_postal_code': segment.pid_11.pid_11_5.to_er7(),
            'address_country': segment.pid_11.pid_11_6.to_er7(),
            'phone_number': segment.pid_13.pid_13_1.to_er7(),
            'primary_language': segment.pid_15.pid_15_2.to_er7(),
            'marital_status': segment.pid_17.pid_17_1.to_er7(),
        }

    def _parse_pv1_segment(self, segment: Segment) -> dict:
        """Extract patient visit data from an HL7v2 PV1 segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'location_poc': segment.pv1_3.pv1_3_1.to_er7(),
            'location_room': segment.pv1_3.pv1_3_2.to_er7(),
            'location_bed': segment.pv1_3.pv1_3_3.to_er7(),
            'location_facility': segment.pv1_3.pv1_3_4.to_er7(),
            'visit_number': segment.pv1_19.pv1_19_1.to_er7(),
        }

    def _parse_orc_segment(self, segment: Segment) -> dict:
        """Extract common order data from an HL7v2 ORC segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'order_control': segment.orc_1.orc_1_1.to_er7(),
            'filler_order_number': segment.orc_3.orc_3_1.to_er7(),
            'order_status': segment.orc_5.orc_5_1.to_er7(),
            'order_quantity': segment.orc_7.orc_7_1.to_er7(),
            'order_quantity_unit': segment.orc_7.orc_7_1_2.to_er7(),
            'order_interval_pattern': segment.orc_7.orc_7_2_1.to_er7(),
            'order_interval_duration': segment.orc_7.orc_7_2_2.to_er7(),
            'order_duration': segment.orc_7.orc_7_3.to_er7(),
            'order_start_datetime': timezone.make_aware(datetime.strptime(segment.orc_7.orc_7_4.to_er7(), '%Y%m%d%H%M')),
            'order_end_datetime': timezone.make_aware(datetime.strptime(segment.orc_7.orc_7_5.to_er7(), '%Y%m%d%H%M')),
            'order_priority': segment.orc_7.orc_7_6.to_er7(),
            'entered_at': timezone.make_aware(datetime.strptime(segment.orc_9.orc_9_1.to_er7(), '%Y%m%d%H%M%S')),
            'entered_by_id': segment.orc_10.orc_10_1.to_er7(),
            'entered_by_family_name': segment.orc_10.orc_10_2.to_er7(),
            'entered_by_given_name': segment.orc_10.orc_10_3.to_er7(),
            'verified_by_id': segment.orc_11.orc_11_1.to_er7(),
            'verified_by_family_name': segment.orc_11.orc_11_2.to_er7(),
            'verified_by_given_name': segment.orc_11.orc_11_3.to_er7(),
            'ordered_by_id': segment.orc_12.orc_12_1.to_er7(),
            'order_by_family_name': segment.orc_12.orc_12_2.to_er7(),
            'order_by_given_name': segment.orc_12.orc_12_3.to_er7(),
            'effective_at': timezone.make_aware(datetime.strptime(segment.orc_15.orc_15_1.to_er7(), '%Y%m%d%H%M%S')),
        }

    def _parse_rxe_segment(self, segment: Segment) -> dict:
        """Extract pharmacy encoding data from an HL7v2 RXE segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'pharmacy_quantity': segment.rxe_1.rxe_1_1.to_er7(),
            'pharmacy_quantity_unit': segment.rxe_1.rxe_1_2.to_er7(),
            'pharmacy_interval_pattern': segment.rxe_1.rxe_1_2_1.to_er7(),
            'pharmacy_interval_duration': segment.rxe_1.rxe_1_2_2.to_er7(),
            'pharmacy_duration': segment.rxe_1.rxe_1_3.to_er7(),
            'pharmacy_start_datetime': timezone.make_aware(datetime.strptime(segment.rxe_1.rxe_1_4.to_er7(), '%Y%m%d%H%M')),
            'pharmacy_end_datetime': timezone.make_aware(datetime.strptime(segment.rxe_1.rxe_1_5.to_er7(), '%Y%m%d%H%M')),
            'pharmacy_priority': segment.rxe_1.rxe_1_6.to_er7(),
            'give_identifier': segment.rxe_2.rxe_2_1.to_er7(),
            'give_text': segment.rxe_2.rxe_2_2.to_er7(),
            'give_coding_system': segment.rxe_2.rxe_2_3.to_er7(),
            'give_alt_identifier': segment.rxe_2.rxe_2_4.to_er7(),
            'give_alt_text': segment.rxe_2.rxe_2_5.to_er7(),
            'give_alt_coding_system': segment.rxe_2.rxe_2_6.to_er7(),
            'give_amount_maximum': segment.rxe_3.rxe_3_1.to_er7(),
            'give_amount_minimum': segment.rxe_4.rxe_4_1.to_er7(),
            'give_units': segment.rxe_5.rxe_5_1.to_er7(),
            'give_dosage_identifier': segment.rxe_6.rxe_6_1.to_er7(),
            'give_dosage_text': segment.rxe_6.rxe_6_2.to_er7(),
            'give_dosage_coding_system': segment.rxe_6.rxe_6_3.to_er7(),
            # TODO: Do we want to replace the \\E\\.br\\E\\ with a line break character for this piece of text?
            # Raw form looks like: `50 mg = 0.5 mL SC Q24H \\E\\.br\\E\\BLEEDING RISK- ANTICOAGULANT\\E\\.br\\E\\* HIGH ALERT  *`
            'provider_administration_instruction': segment.rxe_7.rxe_7_1.to_er7().replace('\\E\\.br\\E\\', '\n'),
            'dispense_amount': segment.rxe_10.rxe_10_1.to_er7(),
            'dispense_units': segment.rxe_11.rxe_11_1.to_er7(),
            'refills': segment.rxe_12.rxe_12_1.to_er7(),
            'refills_remaining': segment.rxe_16.rxe_16_1.to_er7(),
            'prescription_number': segment.rxe_15.rxe_15_1.to_er7(),
            'refills_dispensed': segment.rxe_17.rxe_17_1.to_er7(),
            'give_per_time': segment.rxe_22.rxe_22_1.to_er7(),
            'give_rate_amount': segment.rxe_23.rxe_23_1.to_er7(),
            'give_rate_identifier': segment.rxe_24.rxe_24_1.to_er7(),
            'give_rate_units': segment.rxe_24.rxe_24_2.to_er7(),
        }

    def _parse_rxc_segment(self, segment: Segment) -> dict:
        """Extract pharmacy component data from an HL7v2 RXC segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'component_type': segment.rxc_1.rxc_1_1.to_er7(),
            'component_identifier': segment.rxc_2.rxc_2_1.to_er7(),
            'component_text': segment.rxc_2.rxc_2_2.to_er7(),
            'component_coding_system': segment.rxc_2.rxc_2_3.to_er7(),
            'component_alt_identifier': segment.rxc_2.rxc_2_4.to_er7(),
            'component_alt_text': segment.rxc_2.rxc_2_5.to_er7(),
            'component_alt_coding_system': segment.rxc_2.rxc_2_6.to_er7(),
            'component_amount': segment.rxc_3.rxc_3_1.to_er7(),
            'component_units': segment.rxc_4.rxc_4_1.to_er7(),
        }

    def _parse_rxr_segment(self, segment: Segment) -> dict:
        """Extract pharmacy route data from an HL7v2 RXR segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'route_identifier': segment.rxr_1.rxr_1_1.to_er7(),
            'route_text': segment.rxr_1.rxr_1_2.to_er7(),
            'route_coding_system': segment.rxr_1.rxr_1_3.to_er7(),
            'route_alt_identifier': segment.rxr_1.rxr_1_4.to_er7(),
            'route_alt_text': segment.rxr_1.rxr_1_5.to_er7(),
            'route_alt_coding_system': segment.rxr_1.rxr_1_6.to_er7(),
            'route_site': segment.rxr_2.rxr_2_1.to_er7(),
            'route_administration_device': segment.rxr_3.rxr_3_1.to_er7(),
            'route_administration_identifier': segment.rxr_4.rxr_4_1.to_er7(),
            'route_administration_text': segment.rxr_4.rxr_4_2.to_er7(),
            'route_administration_coding_system': segment.rxr_4.rxr_4_3.to_er7(),
            'route_administration_alt_identifier': segment.rxr_4.rxr_4_4.to_er7(),
            'route_administration_alt_text': segment.rxr_4.rxr_4_5.to_er7(),
            'route_administration_alt_coding_system': segment.rxr_4.rxr_4_6.to_er7(),
        }

    def _parse_nte_segment(self, segment: Segment) -> dict:
        """Extract note and comment data from an HL7v2 NTE segment.

        Args:
            segment: HL7 segment data

        Returns:
            Parsed patient data
        """
        return {
            'note_id': segment.nte_1.nte_1_1.to_er7(),
            'note_comment_id': segment.nte_2.nte_2_1.to_er7(),
            'note_comment_text': segment.nte_3.nte_3_1.to_er7(),
        }


from io import StringIO  # noqa: E402

# TODO: Remove
def temp_demo_parse():  # noqa: WPS210
    """Provide example usage for testing.

    Just open the Django shell, import this file then call hl7_parser.temp_demo_parse()
    """
    parent_dir = Path(__file__).resolve().parent.parent
    with open(parent_dir.joinpath('tests').joinpath('fixtures').joinpath('marge_pharmacy.hl7v2'), 'r') as file:  # noqa: WPS221, E501
        raw_hl7 = file.read()
    stream = StringIO(raw_hl7)
    parser = HL7Parser()
    json_data = parser.parse(stream)
    print(json_data)
