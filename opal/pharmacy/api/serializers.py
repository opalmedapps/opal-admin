"""Serializers for the API views of the `pharmacy` app."""
from typing import Any

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


class _NestedCodedElementSerializer(CodedElementSerializer):
    """`CodedElement` serializer that supports nested updates.

    The uniqueness constraint on identifer, text, coding_system gets
    evaluated before we can call get_or_create in the parent serializer(s).

    Here we disable this validation manually, knowing that we will handle
    the situation correctly in the calling serializer's create method.

    https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
    """

    class Meta(CodedElementSerializer.Meta):
        validators: list[Any] = []


class PharmacyRouteSerializer(serializers.ModelSerializer[PharmacyRoute]):
    """Serializer for the `PharmacyRoute` model."""

    route = _NestedCodedElementSerializer(
        fields=('identifier', 'text', 'coding_system'),
        many=False,
        required=False,
    )
    administration_method = _NestedCodedElementSerializer(
        fields=('identifier', 'text', 'coding_system'),
        many=False,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = PharmacyRoute
        fields = (
            'route',
            'site',
            'administration_device',
            'administration_method',
        )

    def to_internal_value(self, data: Any) -> Any:
        """Check if all fields of `administration_method` are blank and set it to None if true.

        This is required because for the majority of pharmacy data (and in the RxTFC docs), `administration_method`
        is required and present in the HL7.
        But in some special instances, the hospital can send data with an admin_method that has all blank sub-fields

        This will be parsed as a dictionary with keys pointing to blanks, which is technically not null. So we have to
        check for that situation and None the entire administration_method object to avoid a validation error.

        Args:
            data: initial_data to be passed to the internal serializer validation

        Returns:
            Native value for the serializer
        """
        administration_method = data.get('administration_method', {})
        # Check if all subfields of `administration_method` are blank
        if all(not administration_method.get(field) for field in ('identifier', 'text', 'coding_system')):
            data['administration_method'] = None  # Set to None if all subfields are blank
        return super().to_internal_value(data)


class PharmacyComponentSerializer(serializers.ModelSerializer[PharmacyComponent]):
    """Serializer for the `PharmacyComponent` model."""

    component_code = _NestedCodedElementSerializer(
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

    give_code = _NestedCodedElementSerializer(
        many=False,
        required=False,
    )
    give_dosage_form = _NestedCodedElementSerializer(
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

    # TODO: ...Should we fix this related_name? this seems silly
    pharmacy_encoded_order_physician_prescription_order = PharmacyEncodedOrderSerializer(  # noqa: WPS118
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

    def create(self, validated_data: dict[str, Any]) -> PhysicianPrescriptionOrder:  # noqa: WPS210
        """Create new `PhysicianPrescriptionOrder` instance and related model instances.

        Args:
            validated_data: Formattted data from the HL7Parser

        Returns:
            Prescription order instance
        """
        # Extract the nested data
        pharmacy_encoded_order_data = validated_data.pop('pharmacy_encoded_order_physician_prescription_order')
        pharmacy_components_data = pharmacy_encoded_order_data.pop('pharmacy_components')
        pharmacy_route_data = pharmacy_encoded_order_data.pop('pharmacy_route')

        # Create the PhysicianPrescriptionOrder instance
        physician_prescription_order_instance = PhysicianPrescriptionOrder.objects.create(**validated_data)

        # Create the PharmacyEncodedOrder instance and its nested CodedElements
        give_code_data = pharmacy_encoded_order_data.pop('give_code')

        give_code_coded_element_instance, _ = CodedElement.objects.get_or_create(**give_code_data)

        give_dosage_form_data = pharmacy_encoded_order_data.pop('give_dosage_form')
        give_dosage_form_coded_element_instance, _ = CodedElement.objects.get_or_create(
            **give_dosage_form_data,
        )

        pharmacy_encoded_order_instance = PharmacyEncodedOrder.objects.create(
            physician_prescription_order=physician_prescription_order_instance,
            give_code=give_code_coded_element_instance,
            give_dosage_form=give_dosage_form_coded_element_instance,
            **pharmacy_encoded_order_data,
        )

        # Create the PharmacyRoute, including route and administration_method CodedElements
        route_data = pharmacy_route_data.pop('route')
        route_coded_element_instance, _ = CodedElement.objects.get_or_create(**route_data)
        administration_method_data = pharmacy_route_data.pop('administration_method')

        administration_method_coded_element = None
        if administration_method_data:
            administration_method_coded_element, _ = CodedElement.objects.get_or_create(
                **administration_method_data,
            )

        PharmacyRoute.objects.create(
            pharmacy_encoded_order=pharmacy_encoded_order_instance,
            route=route_coded_element_instance,
            administration_method=administration_method_coded_element,
            **pharmacy_route_data,
        )

        # Handle the creation of PharmacyComponents
        for component_data in pharmacy_components_data:
            component_code_data = component_data.pop('component_code')
            component_code_instance, _ = CodedElement.objects.get_or_create(**component_code_data)
            PharmacyComponent.objects.create(
                pharmacy_encoded_order=pharmacy_encoded_order_instance,
                component_code=component_code_instance,
                **component_data,
            )

        return physician_prescription_order_instance
