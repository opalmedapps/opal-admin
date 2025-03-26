"""Module providing API views for the `pharmacy` app."""
import uuid
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response

from opal.core.api.views import HL7CreateView
from opal.core.drf_permissions import IsInterfaceEngine
from opal.hospital_settings.models import Site
from opal.patients.models import Patient

from .serializers import PhysicianPrescriptionOrderSerializer


class CreatePrescriptionView(HL7CreateView):
    """`HL7CreateView` for handling POST requests to create prescription pharmacy data."""

    segments_to_parse = ('PID', 'PV1', 'ORC', 'RXE', 'RXR', 'RXC', 'NTE')
    serializer_class = PhysicianPrescriptionOrderSerializer
    permission_classes = (IsInterfaceEngine,)

    @transaction.atomic
    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        """Extract and transform the parsed data from the request.

        Args:
            request: The http request object
            args: Any number of additional arguments
            kwargs: Any number of key word arguments

        Returns:
            API Response with code and headers
        """
        transformed_data = self._transform_parsed_to_serializer_structure(request.data)  # type: ignore[attr-defined]
        if not self._validate_uuid_matches_pid_segment(request.data, self.kwargs['uuid']):  # type: ignore[attr-defined]
            return Response(
                {
                    'status': 'error',
                    'message': 'PID segment data did not match uuid provided in url.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient: Patient = get_object_or_404(Patient, uuid=self.kwargs['uuid'])
        transformed_data['patient'] = patient.pk
        serializer = self.get_serializer(data=transformed_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _validate_uuid_matches_pid_segment(
        self,
        parsed_data: dict[str, Any],
        url_uuid: uuid.UUID,
    ) -> bool:
        """Ensure the PID segment parsed from the message matches the uuid from the url.

        Args:
            parsed_data: segmented dictionary parsed from the HL7 request data
            url_uuid: UUID string passed in the endpoint url kwarg

        Raises:
            ValidationError: If no patient could be found at all, or multiple are found

        Returns:
            True if the patient identified in the PID segment exists in Django and matches the url uuid
        """
        # Filter out invalid sites from the raw site list given by the hospital (e.g `HNAM_PERSONID`)
        valid_sites = {site_tuple[0] for site_tuple in Site.objects.all().values_list('acronym')}
        valid_pid_mrn_sites = [
            mrn_site for mrn_site in parsed_data.get('PID', None)['mrn_sites'] if mrn_site[1] in valid_sites
        ]
        try:
            patient = Patient.objects.get_patient_by_site_mrn_list(
                site_mrn_list=[
                    {
                        'site': {'acronym': site},
                        'mrn': mrn,
                    } for mrn, site in valid_pid_mrn_sites
                ],
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise ValidationError('Patient identified by HL7 PID could not be uniquely found in database.')
        return url_uuid == patient.uuid

    def _transform_parsed_to_serializer_structure(self, parsed_data: dict[str, Any]) -> dict[str, Any]:  # noqa: WPS210
        """Transform the parsed defaultdict segment data into the expected structure for the serializer.

        Args:
            parsed_data: segmented dictionary parsed from the HL7 request data

        Returns:
            formatted dictionary for internal representation serializer
        """
        order_data = parsed_data['ORC'][0]
        patient_visit_data = parsed_data['PV1'][0]
        pharmacy_encoded_data = parsed_data['RXE'][0]
        note_data = parsed_data['NTE'][0]
        components = parsed_data['RXC']
        route = parsed_data['RXR'][0]
        return {
            'quantity': order_data['order_quantity'],
            'unit': order_data['order_quantity_unit'],
            'interval_pattern': order_data['order_interval_pattern'],
            'interval_duration': order_data['order_interval_duration'],
            'duration': order_data['order_duration'],
            'service_start': order_data['order_start_datetime'],
            'service_end': order_data['order_end_datetime'],
            'priority': order_data['order_priority'],
            'visit_number': patient_visit_data['visit_number'],
            'trigger_event': order_data['order_control'],
            'filler_order_number': order_data['filler_order_number'],
            'order_status': order_data['order_status'],
            'entered_at': order_data['entered_at'],
            'entered_by': '{0}_{1}_{2}'.format(
                order_data['entered_by_given_name'],
                order_data['entered_by_family_name'],
                order_data['entered_by_id'],
            ),
            'verified_by': '{0}_{1}_{2}'.format(
                order_data['verified_by_given_name'],
                order_data['verified_by_family_name'],
                order_data['verified_by_id'],
            ),
            'ordered_by': '{0}_{1}_{2}'.format(
                order_data['order_by_given_name'],
                order_data['order_by_family_name'],
                order_data['ordered_by_id'],
            ),
            'effective_at': order_data['effective_at'],
            'pharmacy_encoded_order': {
                'quantity': pharmacy_encoded_data['pharmacy_quantity'],
                'unit': pharmacy_encoded_data['pharmacy_quantity_unit'],
                'interval_pattern': pharmacy_encoded_data['pharmacy_interval_pattern'],
                'interval_duration': pharmacy_encoded_data['pharmacy_interval_duration'],
                'duration': pharmacy_encoded_data['pharmacy_duration'],
                'service_start': pharmacy_encoded_data['pharmacy_start_datetime'],
                'service_end': pharmacy_encoded_data['pharmacy_end_datetime'],
                'priority': pharmacy_encoded_data['pharmacy_priority'],
                'give_code': {
                    'identifier': pharmacy_encoded_data['give_identifier'],
                    'text': pharmacy_encoded_data['give_text'],
                    'coding_system': pharmacy_encoded_data['give_coding_system'],
                    'alternate_identifier': pharmacy_encoded_data['give_alt_identifier'],
                    'alternate_text': pharmacy_encoded_data['give_alt_text'],
                    'alternate_coding_system': pharmacy_encoded_data['give_alt_coding_system'],
                },
                'give_amount_maximum': pharmacy_encoded_data['give_amount_maximum'],
                'give_amount_minimum': pharmacy_encoded_data['give_amount_minimum'],
                'give_units': pharmacy_encoded_data['give_units'],
                'give_dosage_form': {
                    'identifier': pharmacy_encoded_data['give_dosage_identifier'],
                    'text': pharmacy_encoded_data['give_dosage_text'],
                    'coding_system': pharmacy_encoded_data['give_dosage_coding_system'],
                },
                'provider_administration_instruction': pharmacy_encoded_data['provider_administration_instruction'],
                'dispense_amount': pharmacy_encoded_data['dispense_amount'],
                'dispense_units': pharmacy_encoded_data['dispense_units'],
                'refills': pharmacy_encoded_data['refills'],
                'refills_remaining': pharmacy_encoded_data['refills_remaining'],
                'formulary_status': note_data['note_comment_text'],
                'pharmacy_route': {
                    'route': {
                        'identifier': route['route_identifier'],
                        'text': route['route_text'],
                        'coding_system': route['route_coding_system'],
                        'alternate_identifier': route['route_alt_identifier'],
                        'alternate_text': route['route_alt_text'],
                        'alternate_coding_system': route['route_alt_coding_system'],
                    },
                    'site': route['route_site'],
                    'administration_device': route['route_administration_device'],
                    'administration_method': {
                        'identifier': route['route_administration_identifier'],
                        'text': route['route_administration_text'],
                        'coding_system': route['route_administration_coding_system'],
                        'alternate_identifier': route['route_administration_alt_identifier'],
                        'alternate_text': route['route_administration_alt_text'],
                        'alternate_coding_system': route['route_administration_alt_coding_system'],
                    },
                },
                'pharmacy_components': [
                    {
                        'component_code': {
                            'identifier': component['component_identifier'],
                            'text': component['component_text'],
                            'coding_system': component['component_coding_system'],
                            'alternate_identifier': component['component_alt_identifier'],
                            'alternate_text': component['component_alt_text'],
                            'alternate_coding_system': component['component_alt_coding_system'],
                        },
                        'component_units': component['component_units'],
                        'component_type': component['component_type'],
                        'component_amount': component['component_amount'],
                    } for component in components
                ],
            },
        }
