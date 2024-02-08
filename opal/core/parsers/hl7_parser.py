"""Module which provides HL7-parsing into JSON data for any generic HL7 segment-structured message.

Overrides the
"""
import json
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Mapping

from hl7apy.core import Segment
from hl7apy.parser import parse_message
from rest_framework.parsers import BaseParser


class HL7Parser(BaseParser):
    """Parse HL7-v2 messages and return JSON data."""

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
        }
        # Initialize a dictionary to hold the parsed json data
        self.message_json = {name: [] for name in self.segment_parsers.keys()}

    def parse(
        self,
        stream: IO,
        media_type: str | None = 'application/hl7-v2+er7',
        parser_context: Mapping[str, Any] | None = None,
    ) -> json:
        """Parse the incoming bytestream as an HL7v2 message and return JSON.

        Args:
            stream: Incoming byte stream of request data
            media_type: Acceptable data/media type
            parser_context: Additional request metadata to specify parsing functionality

        Returns:
            parsed json data
        """
        # Read the incoming stream into a string
        raw_data = stream.read()
        # Normalize line endings to CR
        hl7_message = raw_data.replace('\r\n', '\r').replace('\n', '\r')
        # Use hl7apy to parse the message, find_groups=False disables the higher level segment grouping
        # For example, find_groups would typically bundles PID and PV1 into their own 'RDE_O01_PATIENT' grouping)
        for segment in parse_message(hl7_message, find_groups=False).children:
            segment_name = segment.name
            # Find the appropriate parsing function based on the segment name
            parse_function = self.segment_parsers.get(segment_name)

            # If a parsing function is defined, use it to parse the segment
            if parse_function:
                self.message_json[segment_name].append(parse_function(segment))

        return self.message_json

    def _parse_pid_segment(self, segment: Segment) -> json:
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
            # TODO: Kill the mrn_sites which aren't in the 'approved list'
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

    def _parse_pv1_segment(self, segment: Segment):
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

    def _parse_orc_segment(self, segment: Segment):
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
            #'order_quantity': segment.orc_7.orc_7_1.to_er7(),
            #'order_quantity_unit': segment.orc_7.orc_7_1.orc_7_1_2.to_er7(),
            'order_quantity': segment.orc_7[1].to_er7() if len(segment.orc_7) >= 2 else None,
            'order_quantity_unit': segment.orc_7[2].to_er7() if len(segment.orc_7) >= 3 else None,
            #'order_interval_pattern': segment.orc_7.orc_7_2.orc_7_2_1.to_er7(),
            #'order_interval_duration': segment.orc_7.orc_7_2.orc_7_2_2.to_er7(),
            'order_duration': segment.orc_7.orc_7_3.to_er7(),
            'order_start_datetime': segment.orc_7.orc_7_4.to_er7(),
            'order_end_datetime': segment.orc_7.orc_7_5.to_er7(),
            'order_priority': segment.orc_7.orc_7_6.to_er7(),
            'entered_at': segment.orc_9.orc_9_1.to_er7(),
            'entered_by_id': segment.orc_10.orc_10_1.to_er7(),
            'entered_by_family_name': segment.orc_10.orc_10_2.to_er7(),
            'entered_by_given_name': segment.orc_10.orc_10_3.to_er7(),
            'verified_by_id': segment.orc_11.orc_11_1.to_er7(),
            'verified_by_family_name': segment.orc_11.orc_11_2.to_er7(),
            'verified_by_given_name': segment.orc_11.orc_11_3.to_er7(),
            'ordered_by_id': segment.orc_12.orc_12_1.to_er7(),
            'order_by_family_name': segment.orc_12.orc_12_2.to_er7(),
            'order_by_given_name': segment.orc_12.orc_12_3.to_er7(),
            'effective_at': segment.orc_15.orc_15_1.to_er7(),
        }

    def _parse_rxe_segment(self, segment: Segment):
        """Extract pharmacy encoding data from an HL7v2 RXE segment."""
        # TODO: Implement RXE parse
        return segment

    def _parse_rxc_segment(self, segment: Segment):
        """Extract pharmacy component data from an HL7v2 RXC segment."""
        # TODO: Implement RXC parse
        return segment

    def _parse_rxr_segment(self, segment: Segment):
        """Extract pharmacy route data from an HL7v2 RXR segment."""
        # TODO: Implement RXR parse
        return segment


from io import StringIO  # noqa: E402


def temp_demo_parse():  # noqa: WPS210
    """Provide example usage.

    Just open the Django shell, import this file then call hl7_parser.demo_parse()

    Note only the PID segment parse function is implemented for now.
    The others will just be the hl7ap7 library's Segment object data type
    """
    parent_dir = Path(__file__).resolve().parent.parent
    with open(parent_dir.joinpath('tests').joinpath('fixtures').joinpath('marge_pharmacy.hl7v2'), 'r') as file:  # noqa: WPS221, E501
        raw_hl7 = file.read()
    stream = StringIO(raw_hl7)
    parser = HL7Parser()
    json_data = parser.parse(stream)
    print(json_data)
