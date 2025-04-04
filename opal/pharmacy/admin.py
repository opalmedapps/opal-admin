# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for pharmacy models."""

from django.contrib import admin

from .models import CodedElement, PharmacyComponent, PharmacyEncodedOrder, PharmacyRoute, PhysicianPrescriptionOrder


@admin.register(PharmacyComponent)
class PharmacyComponentAdmin(admin.ModelAdmin[PharmacyComponent]):
    """PharmacyComponentAdmin."""

    list_display = ('pharmacy_encoded_order', 'component_type', 'component_code', 'component_amount', 'component_units')


@admin.register(PharmacyRoute)
class PharmacyRouteAdmin(admin.ModelAdmin[PharmacyRoute]):
    """PharmacyRouteAdmin."""

    list_display = ('pharmacy_encoded_order', 'route', 'site', 'administration_device', 'administration_method')


@admin.register(PhysicianPrescriptionOrder)
class PhysicianPrescriptionOrderAdmin(admin.ModelAdmin[PhysicianPrescriptionOrder]):
    """PhysicianPrescriptionOrderAdmin."""

    list_display = (
        'patient',
        'trigger_event',
        'filler_order_number',
        'quantity',
        'unit',
        'interval_pattern',
        'interval_duration',
        'duration',
        'service_start',
        'service_end',
        'priority',
        'order_status',
        'entered_at',
        'entered_by',
    )
    ordering = ('patient', '-entered_at')


@admin.register(PharmacyEncodedOrder)
class PharmacyEncodedOrderAdmin(admin.ModelAdmin[PharmacyEncodedOrder]):
    """PharmacyEncodedOrderOrderAdmin."""

    list_display = (
        'physician_prescription_order',
        'give_code',
        'quantity',
        'unit',
        'interval_pattern',
        'interval_duration',
        'duration',
        'service_start',
        'service_end',
        'priority',
        'give_amount_maximum',
        'give_amount_minimum',
        'give_units',
        'give_dosage_form',
        'provider_administration_instruction',
        'dispense_amount',
        'dispense_units',
        'refills',
        'formulary_status',
    )
    ordering = ('physician_prescription_order', '-service_start')


@admin.register(CodedElement)
class CodedElementAdmin(admin.ModelAdmin[CodedElement]):
    """CodedElementAdmin."""

    list_display = (
        'identifier',
        'text',
        'coding_system',
        'alternate_identifier',
        'alternate_text',
        'alternate_coding_system',
    )
    ordering = ('identifier', 'coding_system')
