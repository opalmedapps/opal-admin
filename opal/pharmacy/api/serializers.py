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
        fields=('identifier', 'text', 'coding_system'),
        many=False,
        required=False,
    )
    administration_method = CodedElementSerializer(
        fields=('identifier', 'text', 'coding_system'),
        many=False,
        required=False,
    )

    class Meta:
        model = PharmacyRoute
        fields = (
            'route',
            'site',
            'administration_device',
            'administration_method',
        )


class PharmacyComponentSerializer(serializers.ModelSerializer[PharmacyComponent]):
    """Serializer for the `PharmacyComponent` model."""

    component_code = CodedElementSerializer(
        many=False,
        required=False,
    )

    class Meta:
        model = PharmacyComponent
        fields = (
            'component_code',
            'component_units',
            'component_type',
            'component_amount',
        )


class PharmacyEncodedOrderSerializer(serializers.ModelSerializer[PharmacyEncodedOrder]):
    """Serializer for the `PharmacyEncodedOrder` model."""

    give_code = CodedElementSerializer(
        many=False,
        required=False,
    )
    give_dosage_form = CodedElementSerializer(
        many=False,
        required=False,
    )
    pharmacy_route = PharmacyRouteSerializer(
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
            'quantity',
            'unit',
            'interval_pattern',
            'interval_duration',
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
            'formulary_status',
            'pharmacy_route',
            'pharmacy_components',
        )


class PhysicianPrescriptionOrderSerializer(serializers.ModelSerializer[PhysicianPrescriptionOrder]):
    """Serializer for the `PhysicianPrescriptionOrder` model."""

    pharmacy_encoded_order_physician_prescription_order = PharmacyEncodedOrderSerializer(
        many=False,
        required=True,
    )

    class Meta:
        model = PhysicianPrescriptionOrder
        fields = (
            'patient',
            'pharmacy_encoded_order_physician_prescription_order',
            'quantity',
            'unit',
            'interval_pattern',
            'interval_duration',
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

    def create(self, validated_data):
        # Extract the nested data
        pharmacy_encoded_order_data = validated_data.pop('pharmacy_encoded_order_physician_prescription_order')
        pharmacy_components_data = pharmacy_encoded_order_data.pop('pharmacy_components')
        pharmacy_route_data = pharmacy_encoded_order_data.pop('pharmacy_route')
        print(pharmacy_route_data)
        # Create the PhysicianPrescriptionOrder instance
        physician_prescription_order_instance = PhysicianPrescriptionOrder.objects.create(**validated_data)

        # Create the PharmacyEncodedOrder instance and its nested CodedElements
        give_code_data = pharmacy_encoded_order_data.pop('give_code')

        give_code_coded_element_instance, new_substance = CodedElement.objects.get_or_create(**give_code_data)

        give_dosage_form_data = pharmacy_encoded_order_data.pop('give_dosage_form')
        give_dosage_form_coded_element_instance, new_substance = CodedElement.objects.get_or_create(**give_dosage_form_data)

        pharmacy_encoded_order_instance = PharmacyEncodedOrder.objects.create(
            physician_prescription_order=physician_prescription_order_instance,
            give_code=give_code_coded_element_instance,
            give_dosage_form=give_dosage_form_coded_element_instance,
            **pharmacy_encoded_order_data,
        )

        # Create the PharmacyRoute, including route and administration_method CodedElements
        route_data = pharmacy_route_data.pop('route')
        route_coded_element_instance, new_substance = CodedElement.objects.get_or_create(**route_data)
        administration_method_data = pharmacy_route_data.pop('administration_method')
        administration_method_coded_element, new_substance = CodedElement.objects.get_or_create(**administration_method_data)

        PharmacyRoute.objects.create(
            pharmacy_encoded_order=pharmacy_encoded_order_instance,
            route=route_coded_element_instance,
            administration_method=administration_method_coded_element,
            **pharmacy_route_data,
        )

        # Handle the creation of PharmacyComponents
        for component_data in pharmacy_components_data:
            component_code_data = component_data.pop('component_code')
            component_code_instance, new_substance = CodedElement.objects.get_or_create(**component_code_data)
            PharmacyComponent.objects.create(
                pharmacy_encoded_order=pharmacy_encoded_order_instance,
                component_code=component_code_instance,
                **component_data,
            )

        return physician_prescription_order_instance
