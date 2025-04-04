# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializers for the API views of the `pharmacy` app."""

from typing import Any

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import CodedElement, PharmacyComponent, PharmacyEncodedOrder, PharmacyRoute, PhysicianPrescriptionOrder


def clean_coded_element_internal_blanks(
    serializer_data: dict[str, Any],
    coded_element_fields: list[str],
) -> dict[str, Any]:
    """
    Check if all subfields of a CodedElement instance field are blank and set it to None if true.

    This is required because for the majority of pharmacy data (and in the RxTFC docs), CodedElement fields
    are required and are generally sent correctly in the source system HL7.
    But in some instances, the hospital sends data with all blank subfields within CodedElement instances.
    This will be parsed as a dictionary with keys pointing to blanks, which is technically not null,
    causing an attempted CodedElement model save which will error on the required fields being blank.

    So we have to check for that situation and None the entire instance to avoid a validation error.

    Args:
        serializer_data: initial_data to be passed to the internal serializer validation
        coded_element_fields: list of the CE fields to be checked for internal blanks

    Returns:
        Cleaned data for the serializer
    """
    for ce_field in coded_element_fields:
        ce_data = serializer_data.get(ce_field, {})
        # Check if all required subfields of the CE object are blank
        if all(not ce_data.get(field) for field in ('identifier', 'text', 'coding_system')):
            serializer_data[ce_field] = None  # Set to None if all subfields are blank
    return serializer_data


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
    """
    `CodedElement` serializer that supports nested updates.

    The uniqueness constraint on identifier, text, coding_system gets
    evaluated before we can call get_or_create in the parent serializer(s).

    Here we disable this validation manually, knowing that we will handle
    the situation correctly in the calling serializer's create method.

    https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Dynamically remove just the UniqueTogetherValidator
        self.validators = [
            validator
            for validator in self.validators
            if not (  # type: ignore[redundant-expr]
                isinstance(
                    validator,
                    UniqueTogetherValidator,
                )
                and set(validator.fields) == {'identifier', 'text', 'coding_system'}  # type: ignore[unreachable]
            )
        ]


class PharmacyRouteSerializer(serializers.ModelSerializer[PharmacyRoute]):
    """Serializer for the `PharmacyRoute` model."""

    route = _NestedCodedElementSerializer(
        fields=('identifier', 'text', 'coding_system'),
        many=False,
        required=False,
        allow_null=True,
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
        """
        Properly `None` any optional CE elements before internal validation occurs to avoid error.

        Args:
            data: initial_data to be passed to the internal serializer validation

        Returns:
            Native value for the serializer
        """
        data = clean_coded_element_internal_blanks(data, ['administration_method', 'route'])
        return super().to_internal_value(data)


class PharmacyComponentSerializer(serializers.ModelSerializer[PharmacyComponent]):
    """Serializer for the `PharmacyComponent` model."""

    component_code = _NestedCodedElementSerializer(
        many=False,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = PharmacyComponent
        fields = (
            'component_code',
            'component_units',
            'component_type',
            'component_amount',
        )

    def to_internal_value(self, data: Any) -> Any:
        """
        Properly `None` any optional CE elements before internal validation occurs to avoid error.

        Args:
            data: initial_data to be passed to the internal serializer validation

        Returns:
            Native value for the serializer
        """
        data = clean_coded_element_internal_blanks(data, ['component_code'])
        return super().to_internal_value(data)


class PharmacyEncodedOrderSerializer(serializers.ModelSerializer[PharmacyEncodedOrder]):
    """Serializer for the `PharmacyEncodedOrder` model."""

    give_code = _NestedCodedElementSerializer(
        many=False,
        required=False,
        allow_null=True,
    )
    give_dosage_form = _NestedCodedElementSerializer(
        many=False,
        required=False,
        allow_null=True,
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
            'formulary_status',
            'pharmacy_route',
            'pharmacy_components',
        )

    def to_internal_value(self, data: Any) -> Any:
        """
        Properly `None` any optional CE elements before internal validation occurs to avoid error.

        Args:
            data: initial_data to be passed to the internal serializer validation

        Returns:
            Native value for the serializer
        """
        data = clean_coded_element_internal_blanks(data, ['give_dosage_form', 'give_code'])
        return super().to_internal_value(data)


class PhysicianPrescriptionOrderSerializer(serializers.ModelSerializer[PhysicianPrescriptionOrder]):
    """Serializer for the `PhysicianPrescriptionOrder` model."""

    pharmacy_encoded_order = PharmacyEncodedOrderSerializer(
        many=False,
        required=True,
    )

    class Meta:
        model = PhysicianPrescriptionOrder
        fields = (
            'patient',
            'pharmacy_encoded_order',
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

    def create(self, validated_data: dict[str, Any]) -> PhysicianPrescriptionOrder:  # noqa: PLR0914
        """
        Create new `PhysicianPrescriptionOrder` instance and related model instances.

        Args:
            validated_data: Formatted data from the HL7Parser

        Returns:
            Prescription order instance
        """
        # Extract the nested data
        pharmacy_encoded_order_data = validated_data.pop('pharmacy_encoded_order')
        pharmacy_components_data = pharmacy_encoded_order_data.pop('pharmacy_components')
        pharmacy_route_data = pharmacy_encoded_order_data.pop('pharmacy_route')

        # Create the PhysicianPrescriptionOrder instance
        physician_prescription_order_instance = PhysicianPrescriptionOrder.objects.create(**validated_data)

        # Create the PharmacyEncodedOrder instance and its nested CodedElements
        give_code_data = pharmacy_encoded_order_data.pop('give_code')
        give_code_coded_element = None
        if give_code_data:
            give_code_coded_element, _ = CodedElement.objects.get_or_create(**give_code_data)

        give_dosage_form_data = pharmacy_encoded_order_data.pop('give_dosage_form')
        give_dosage_form_coded_element = None
        if give_dosage_form_data:
            give_dosage_form_coded_element, _ = CodedElement.objects.get_or_create(
                **give_dosage_form_data,
            )

        pharmacy_encoded_order_instance = PharmacyEncodedOrder.objects.create(
            physician_prescription_order=physician_prescription_order_instance,
            give_code=give_code_coded_element,
            give_dosage_form=give_dosage_form_coded_element,
            **pharmacy_encoded_order_data,
        )

        # Create the PharmacyRoute, including route and administration_method CodedElements
        route_data = pharmacy_route_data.pop('route')
        route_coded_element = None
        if route_data:
            route_coded_element, _ = CodedElement.objects.get_or_create(**route_data)

        administration_method_data = pharmacy_route_data.pop('administration_method')
        administration_method_coded_element = None
        if administration_method_data:
            administration_method_coded_element, _ = CodedElement.objects.get_or_create(
                **administration_method_data,
            )

        PharmacyRoute.objects.create(
            pharmacy_encoded_order=pharmacy_encoded_order_instance,
            route=route_coded_element,
            administration_method=administration_method_coded_element,
            **pharmacy_route_data,
        )

        # Handle the creation of PharmacyComponents
        for component_data in pharmacy_components_data:
            component_code_data = component_data.pop('component_code')
            component_code_element = None
            if component_code_data:
                component_code_element, _ = CodedElement.objects.get_or_create(**component_code_data)
            PharmacyComponent.objects.create(
                pharmacy_encoded_order=pharmacy_encoded_order_instance,
                component_code=component_code_element,
                **component_data,
            )

        return physician_prescription_order_instance
