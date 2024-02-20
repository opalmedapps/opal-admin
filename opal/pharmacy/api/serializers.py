"""Serializers for the API views of the `pharmacy` app."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import CodedElement, PharmacyComponent, PharmacyEncodedOrder, PharmacyRoute, PhysicianPrescriptionOrder


class CodedElementSerializer(DynamicFieldsSerializer[CodedElement]):
    """Serializer for the `CodedElement` model."""

    class Meta:
        model = CodedElement
        fields = (
            'identifier',
            'text',
            'coding_system',
            'alternate_identifier',
            'alternate_text',
            'alternate_coding_system',
        )


class PharmacyRouteSerializer(serializers.ModelSerializer[PharmacyRoute]):
    """Serializer for the `PharmacyRoute` model."""

    route = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    site = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    administration_device = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    administration_method = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )

    class Meta:
        model = PharmacyRoute
        fields = (
            'pharmacy_encoded_order',
            'route',
            'site',
            'administration_device',
            'administration_method',
        )


class PharmacyComponentSerializer(serializers.ModelSerializer[PharmacyComponent]):
    """Serializer for the `PharmacyComponent` model."""

    component_code = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    component_units = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )

    class Meta:
        model = PharmacyComponent
        fields = (
            'pharmacy_encoded_order',
            'component_code',
            'component_units',
            'component_type',
            'component_amount',
        )


class PharmacyEncodedOrderSerializer(serializers.ModelSerializer[PharmacyEncodedOrder]):
    """Serializer for the `PharmacyEncodedOrder` model."""

    give_code = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    give_units = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    give_dosage_form = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    provider_administration_instruction = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    dispense_units = CodedElementSerializer(
        fields='__all__',
        many=False,
        required=False,
    )
    pharmacy_routes = PharmacyRouteSerializer(
        many=False,
        required=True,
    )
    pharmacy_components = PharmacyComponentSerializer(
        many=True,
        required=True,
    )

    class Meta:
        model = PharmacyEncodedOrder
        fields = (
            'physician_prescription_order',
            'quantity',
            'unit',
            'interval',
            'duration',
            'service_start',
            'service_end',
            'priority',
            'give_code',
            'give_amount_maximum',
            'give_amount_minimum',
            'give_units',
            'give_dosage_form',
            'provider_administration_instruction',
            'dispense_amount',
            'dispense_units',
            'refills',
            'refills_remaining',
            'last_refilled',
            'formulary_status',
            'pharmacy_route',
            'pharmacy_components',
        )


class PhysicianPrescriptionOrderSerializer(serializers.ModelSerializer[PhysicianPrescriptionOrder]):
    """Serializer for the `PhysicianPrescriptionOrder` model."""

    class Meta:
        model = PhysicianPrescriptionOrder
        fields = (
            'patient',
            'quantity',
            'unit',
            'interval',
            'duration',
            'service_start',
            'service_end',
            'priority',
            'visit_number',
            'trigger_event',
            'filler_order_number',
            'order_status',
            'entered_at',
            'entered_by',
            'verified_by',
            'ordered_by',
            'effective_at',
        )
