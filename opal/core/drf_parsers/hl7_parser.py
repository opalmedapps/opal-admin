"""Module which provides HL7-parsing into JSON data for any generic HL7 segment-structured message."""
from collections import defaultdict
from datetime import datetime
from typing import IO, Any, Callable, Mapping, TypeAlias

from django.utils import timezone

from hl7apy.core import Segment
from hl7apy.parser import parse_message
from rest_framework import exceptions
from rest_framework.parsers import BaseParser

ParserFunction: TypeAlias = Callable[[Segment], dict[str, Any]]

FORMAT_DATE = '%Y%m%d'
FORMAT_DATETIME_SHORT = '%Y%m%d%H%M'
FORMAT_DATETIME_COMPLETE = '%Y%m%d%H%M%S'


def parse_pid_segment(segment: Segment) -> dict[str, Any]:
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
        'date_of_birth': datetime.strptime(segment.pid_7.to_er7(), FORMAT_DATE).date(),
        'sex': segment.pid_8.to_er7(),
        'ramq': segment.pid_2.pid_2_1.to_er7(),
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


def parse_pv1_segment(segment: Segment) -> dict[str, Any]:
    """Extract patient visit data from an HL7v2 PV1 segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/PV1

    Args:
        segment: HL7 segment data

    Returns:
        Parsed patient visit data
    """
    return {
        'location_poc': segment.pv1_3.pv1_3_1.to_er7(),
        'location_room': segment.pv1_3.pv1_3_2.to_er7(),
        'location_bed': segment.pv1_3.pv1_3_3.to_er7(),
        'location_facility': segment.pv1_3.pv1_3_4.to_er7(),
        'visit_number': segment.pv1_19.pv1_19_1.to_er7(),
    }


def parse_orc_segment(segment: Segment) -> dict[str, Any]:
    """Extract common order data from an HL7v2 ORC segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/ORC

    Args:
        segment: HL7 segment data

    Returns:
        Parsed order control data
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
        'order_start_datetime': parse_datetime_from_er7(segment.orc_7.orc_7_4.to_er7(), FORMAT_DATETIME_SHORT),
        'order_end_datetime': parse_datetime_from_er7(segment.orc_7.orc_7_5.to_er7(), FORMAT_DATETIME_SHORT),
        'order_priority': segment.orc_7.orc_7_6.to_er7(),
        'entered_at': parse_datetime_from_er7(segment.orc_9.orc_9_1.to_er7(), FORMAT_DATETIME_COMPLETE),
        'entered_by_id': segment.orc_10.orc_10_1.to_er7(),
        'entered_by_family_name': segment.orc_10.orc_10_2.to_er7(),
        'entered_by_given_name': segment.orc_10.orc_10_3.to_er7(),
        'verified_by_id': segment.orc_11.orc_11_1.to_er7(),
        'verified_by_family_name': segment.orc_11.orc_11_2.to_er7(),
        'verified_by_given_name': segment.orc_11.orc_11_3.to_er7(),
        'ordered_by_id': segment.orc_12.orc_12_1.to_er7(),
        'order_by_family_name': segment.orc_12.orc_12_2.to_er7(),
        'order_by_given_name': segment.orc_12.orc_12_3.to_er7(),
        'effective_at': parse_datetime_from_er7(segment.orc_15.orc_15_1.to_er7(), FORMAT_DATETIME_COMPLETE),
    }


def parse_rxe_segment(segment: Segment) -> dict[str, Any]:
    """Extract pharmacy encoding data from an HL7v2 RXE segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXE

    Args:
        segment: HL7 segment data

    Returns:
        Parsed pharmacy encoding data
    """
    return {
        'pharmacy_quantity': segment.rxe_1.rxe_1_1.to_er7(),
        'pharmacy_quantity_unit': segment.rxe_1.rxe_1_1_2.to_er7(),
        'pharmacy_interval_pattern': segment.rxe_1.rxe_1_2_1.to_er7(),
        'pharmacy_interval_duration': segment.rxe_1.rxe_1_2_2.to_er7(),
        'pharmacy_duration': segment.rxe_1.rxe_1_3.to_er7(),
        'pharmacy_start_datetime': parse_datetime_from_er7(segment.rxe_1.rxe_1_4.to_er7(), FORMAT_DATETIME_SHORT),
        'pharmacy_end_datetime': parse_datetime_from_er7(segment.rxe_1.rxe_1_5.to_er7(), FORMAT_DATETIME_SHORT),
        'pharmacy_priority': segment.rxe_1.rxe_1_6.to_er7(),
        'give_identifier': segment.rxe_2.rxe_2_1.to_er7(),
        'give_text': segment.rxe_2.rxe_2_2.to_er7(),
        'give_coding_system': segment.rxe_2.rxe_2_3.to_er7(),
        'give_alt_identifier': segment.rxe_2.rxe_2_4.to_er7(),
        'give_alt_text': segment.rxe_2.rxe_2_5.to_er7(),
        'give_alt_coding_system': segment.rxe_2.rxe_2_6.to_er7(),
        'give_amount_minimum': segment.rxe_3.rxe_3_1.to_er7(),
        'give_amount_maximum': segment.rxe_4.rxe_4_1.to_er7(),
        'give_units': segment.rxe_5.rxe_5_1.to_er7(),
        'give_dosage_identifier': segment.rxe_6.rxe_6_1.to_er7(),
        'give_dosage_text': segment.rxe_6.rxe_6_2.to_er7(),
        'give_dosage_coding_system': segment.rxe_6.rxe_6_3.to_er7(),
        'provider_administration_instruction': fix_breaking_characters(segment.rxe_7.rxe_7_1.to_er7()),
        'dispense_amount': segment.rxe_10.rxe_10_1.to_er7(),
        'dispense_units': segment.rxe_11.rxe_11_1.to_er7(),
        'refills': segment.rxe_12.rxe_12_1.to_er7(),
        'prescription_number': segment.rxe_15.rxe_15_1.to_er7(),
        'refills_dispensed': segment.rxe_17.rxe_17_1.to_er7(),
        'give_per_time': segment.rxe_22.rxe_22_1.to_er7(),
        'give_rate_amount': segment.rxe_23.rxe_23_1.to_er7(),
        'give_rate_identifier': segment.rxe_24.rxe_24_1.to_er7(),
        'give_rate_units': segment.rxe_24.rxe_24_2.to_er7(),
    }


def parse_rxc_segment(segment: Segment) -> dict[str, Any]:
    """Extract pharmacy component data from an HL7v2 RXC segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXC

    Args:
        segment: HL7 segment data

    Returns:
        Parsed pharmacy component data
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


def parse_rxr_segment(segment: Segment) -> dict[str, Any]:
    """Extract pharmacy route data from an HL7v2 RXR segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXR

    Args:
        segment: HL7 segment data

    Returns:
        Parsed pharmacy route data
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


def parse_nte_segment(segment: Segment) -> dict[str, Any]:
    """Extract note and comment data from an HL7v2 NTE segment.

    https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/NTE

    Args:
        segment: HL7 segment data

    Returns:
        Parsed note data
    """
    return {
        'note_id': segment.nte_1.nte_1_1.to_er7(),
        'note_comment_id': segment.nte_2.nte_2_1.to_er7(),
        'note_comment_text': segment.nte_3.nte_3_1.to_er7(),
    }


def parse_datetime_from_er7(field: str, isoformat: str) -> datetime:
    """Convert HL7-er7 format to timezone-aware datetime.

    Args:
        field: Extracted HL7 field from the message
        isoformat: Isoformat for the datetime function

    Returns:
        Formatted datetime object
    """
    return timezone.make_aware(datetime.strptime(field, isoformat))


def fix_breaking_characters(field: str) -> str:
    """Replace incorrectly encoded or interpretted characters with linebreaks.

    Args:
        field: The HL7 er7 data to be cleaned

    Returns:
        replaced string
    """
    return field.replace('\\E\\.br\\E\\', '\n')  # noqa: WPS342


class HL7Parser(BaseParser):
    """Parse HL7-v2 messages and return dictionary data."""

    media_type = 'application/hl7-v2+er7'
    segment_parsers: dict[str, ParserFunction] = {
        'PID': parse_pid_segment,
        'PV1': parse_pv1_segment,
        'ORC': parse_orc_segment,
        'RXE': parse_rxe_segment,
        'RXC': parse_rxc_segment,
        'RXR': parse_rxr_segment,
        'NTE': parse_nte_segment,
    }

    def parse(  # noqa: WPS210, WPS234, C901
        self,
        stream: IO[Any],
        media_type: str | None = None,
        parser_context: Mapping[str, Any] | None = None,
    ) -> dict[Any, list[dict[str, Any]]]:
        """Parse the incoming bytestream as an HL7v2 message and return JSON.

        Args:
            stream: Incoming byte stream of request data
            media_type: Acceptable data/media type
            parser_context: Additional request metadata to specify parsing functionality

        Raises:
            ParseError: If the data passed is not a StringIO stream

        Returns:
            dictionary object containing the parsed HL7v2 message
        """
        # Initialize the message_dict to hold parsed data
        message_dict: dict[str, Any] = defaultdict(list)

        # Read the incoming stream into a string
        try:
            raw_data_bytes = stream.read()
        except AttributeError:
            raise exceptions.ParseError('Request data must be application/hl7v2+er7 string stream')

        # Decode the bytes object to a string for further processing
        try:
            raw_data_str = raw_data_bytes.decode('utf-8')
        except AttributeError as err:
            raise exceptions.ParseError(f'Error decoding HL7 message: {err}')

        # Normalize line endings to CR
        hl7_message = raw_data_str.replace('\r\n', '\r').replace('\n', '\r')
        # Check for a parser context which defines specific segments to be parsed
        segments_to_parse = parser_context.get('segments_to_parse') if parser_context else None

        # Use hl7apy to parse the message, find_groups=False disables the higher level segment grouping
        # For example, find_groups would typically bundles PID and PV1 into their own 'RDE_O01_PATIENT' grouping)
        for segment in parse_message(hl7_message, find_groups=False).children:
            segment_name = segment.name

            # Skip parsing this segment if segments_to_parse is set and does not request this segment
            if segments_to_parse and segment_name not in segments_to_parse:
                continue

            # Find the appropriate parsing function based on the segment name
            parse_function = self.segment_parsers.get(segment_name)
            # If a parsing function is defined, use it to parse the segment
            if parse_function and segment_name == 'PID':
                # Only 1 PID segment is ever expected
                message_dict[segment_name] = parse_function(segment)
            elif parse_function:
                # Other segment types can have multiple
                message_dict[segment_name].append(parse_function(segment))

        return message_dict
