"""Module which provides hl7-parsing into json data for any generic HL7 segment-structured message.

In theory this could be used for any generic HL7 message to extract json

My thinking is we could call this parsing utility directly in each app's API view/serializer
and use the json from this utility as the 'validated_data' for the model serializer

This would make this utility fairly re-usable and scalable. We can implement more
parsing functions as we choose to expand the utility. For now, we would just need parsing for
PID, ORC, RXE, RXR, and RXC. That covers all the requirements for pharmacy.

In the future we can add parsing for OBR, OBX, PV1, NTE, for example, to allow parsing of lab messages and pathology.

Each API endpoint only needs to use the parsed segments it needs for its data.
We could also implement functions in this utility
to match a parsed hl7 segment to an existing model (for example, take the parsed PID segment json data
and find the existing Patient object)
"""
from datetime import datetime
from pathlib import Path

from hl7apy.core import Segment
from hl7apy.parser import parse_message

UTILS_DIR = Path(__file__).resolve().parent


class HL7Parser:
    """Util which provides functionality for handling HL7 text data and parsing."""

    def __init__(self):
        """Initialize the segment parsing functions."""
        self.segment_parsers: dict[str, function] = {
            'PID': self.parse_pid_segment,
            'ORC': self.parse_orc_segment,
            'RXE': self.parse_rxe_segment,
            'RXC': self.parse_rxc_segment,
            'RXR': self.parse_rxr_segment,
            # Add other segment parsers here to expand functionality
        }
        # Initialize a dictionary to hold the parsed json data
        self.message_json = {name: [] for name in self.segment_parsers.keys()}

    def parse_pid_segment(self, segment: Segment):
        """Extract patient data from an HL7v2 PID segment.

        Use the HL7 documentation to know which fields contain the correct data:
        https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/PID
        """
        return {
            'first_name': segment.pid_5.pid_5_2.to_er7(),
            'last_name': segment.pid_5.pid_5_1.to_er7(),
            'date_of_birth': datetime.strptime(segment.pid_7.to_er7(), '%Y%m%d').date(),
            'sex': segment.pid_8.to_er7(),
            'ramq': segment.pid_2.pid_2_1.to_er7(),
            'mrn_sites': [(mrn_site.pid_3_1.to_er7(), mrn_site.pid_3_4.to_er7()) for mrn_site in segment.pid_3],
            # can further extract address, phone number, primary language, etc from the hl7 if desired
        }

    def parse_orc_segment(self, segment: Segment):
        """Extract common order data from an HL7v2 ORC segment."""
        # TODO: Implement ORC parse
        return segment

    def parse_rxe_segment(self, segment: Segment):
        """Extract pharmacy encoding data from an HL7v2 RXE segment."""
        # TODO: Implement RXE parse
        return segment

    def parse_rxc_segment(self, segment: Segment):
        """Extract pharmacy component data from an HL7v2 RXC segment."""
        # TODO: Implement RXC parse
        return segment

    def parse_rxr_segment(self, segment: Segment):
        """Extract pharmacy route data from an HL7v2 RXR segment."""
        # TODO: Implement RXR parse
        return segment

    def parse_hl7_message_to_json(self, hl7_message: Segment):
        """Parse function to return the parsed json message."""
        # Normalize line endings to CR
        hl7_message = hl7_message.replace('\r\n', '\r').replace('\n', '\r')
        # Use hl7apy to parse the message, find_groups=False disables the higher level segment grouping
        # For example, find_groups would typically bundles PID and PV1 into their own 'RDE_O01_PATIENT' grouping)
        parsed_message = parse_message(hl7_message, find_groups=False)
        # Iterate through each segment in the parsed message
        for segment in parsed_message.children:
            segment_name = segment.name
            # Find the appropriate parsing function based on the segment name
            parse_function = self.segment_parsers.get(segment_name)

            # If a parsing function is defined, use it to parse the segment
            if parse_function:
                self.message_json[segment_name].append(parse_function(segment))

        return self.message_json


def demo_parse():
    """Provide example usage.

    Just open the Django shell, import this file then call hl7_parser.demo_parse()

    Note only the PID segment parse function is implemented for now.
    The others will just be the hl7ap7 library's Segment object data type
    """
    with open(UTILS_DIR.joinpath('marge_pharmacy.hl7v2'), 'r') as file:
        raw_hl7 = file.read()
    parser = HL7Parser()
    json_data = parser.parse_hl7_message_to_json(raw_hl7)
    print(json_data)
