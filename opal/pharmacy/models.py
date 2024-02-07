"""Module providing models for pharmacy data."""
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


class AbstractQuantityTiming(models.Model):
    """Describes the quantity and timing information for a given prescription/order.

    Quantity/Timing specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Fields/ORC.7

    The default duration is indefinite which can also be taken to mean 'until the prescription runs out.
    The default priority is Routine/Default: https://hl7-definition.caristix.com/v2/HL7v2.3/Fields/ORC.7.6
    """

    quantity = models.DecimalField(max_digits=8, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)
    interval = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, default='INDEF')
    service_start = models.DateTimeField(blank=True)
    service_end = models.DateTimeField(blank=True)
    priority = models.CharField(max_length=10, default='R')

    class Meta:
        abstract = True


class PhysicianPrescriptionOrder(AbstractQuantityTiming):
    """Describes the physician's prescription/order in its original state.

    Common Order Segment specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/ORC
    """

    patient = models.ForeignKey(
        verbose_name=_('Patient'),
        to=Patient,
        on_delete=models.CASCADE,
        related_name='physician_prescriptions',
    )
    trigger_event = models.CharField(max_length=2)
    filler_order_number = models.IntegerField()
    order_status = models.CharField(max_length=2, default='SC')
    entered_at = models.DateTimeField()
    entered_by = models.CharField(max_length=75)
    verified_by = models.CharField(max_length=75)
    ordered_by = models.CharField(max_length=75)
    effective_at = models.DateTimeField()

    class Meta:
        verbose_name = _('Physician Prescription')
        verbose_name_plural = _('Physician Prescriptions')

    def __str__(self):
        """Provide string representation.

        Returns:
            string representation
        """
        return f'Prescription Order {self.id} for Patient {self.patient.id}'


class PharmacyEncodedOrder(AbstractQuantityTiming):
    """Describes the final prescription/order after any alterations mandated by the pharmacy provider.

    Pharmacy Encoded Order specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXE
    """

    physician_prescription_order = models.ForeignKey('PhysicianPrescriptionOrder', on_delete=models.CASCADE)
    give_code = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_give_code',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    give_amount_maximum = models.DecimalField(null=True, blank=True, max_digits=8, decimal_places=3)
    give_amount_minimum = models.DecimalField(max_digits=8, decimal_places=3)
    give_units = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_give_units',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    give_dosage_form = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_give_dosage_form',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    provider_administration_instruction = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_provider_administration_instruction',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    dispense_amount = models.DecimalField(max_digits=8, decimal_places=3)
    dispense_units = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_dispense_units',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    refills = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)
    last_refilled = models.DateTimeField(blank=True)
    formulary_status = models.CharField(max_length=10)

    class Meta:
        verbose_name = _('Pharmacy Encoding')
        verbose_name_plural = _('Pharmacy Encodings')

    def __str__(self):
        """Provide string representation.

        Returns:
            string representation
        """
        return f'Encoded Order {self.id} for Prescription {self.physician_prescription_order_id}'


class CodedElement(models.Model):
    """A uniquely identified substance within some pharmaceutical coding system.

    Coded Element Data Type specifications:https://hl7-definition.caristix.com/v2/HL7v2.3/DataTypes/CE
    """

    identifier = models.CharField(max_length=50)
    text = models.CharField(max_length=150)
    coding_system = models.CharField(max_length=50)
    alternate_identifier = models.CharField(max_length=50, blank=True)
    alternate_text = models.CharField(max_length=150, blank=True)
    alternate_coding_system = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = _('Coded Element')
        verbose_name_plural = _('Coded Elements')
        unique_together = (('identifier', 'coding_system'),)

    def __str__(self):
        """Provide string representation.

        Returns:
            string representation
        """
        return f'{self.text} ({self.identifier} - {self.coding_system})'


class PharmacyRoute(models.Model):
    """Special pharmacy-provided instructions for the method of delivery of a prescription/order.

    Pharmacy Route specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXR
    """

    pharmacy_encoded_order = models.ForeignKey('PharmacyEncodedOrder', on_delete=models.CASCADE)
    route = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_route_route',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    site = models.ForeignKey(
        'CodedElement',
        null=True,
        blank=True,
        related_name='pharmacy_route_site',
        on_delete=models.SET_NULL,
    )
    administration_device = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_route_administration_device',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    administration_method = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_route_administration_method',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _('Pharmacy Route')
        verbose_name_plural = _('Pharmacy Routes')

    def __str__(self):
        """Provide string representation.

        Returns:
            string representation
        """
        return f'Route for Order {self.pharmacy_encoded_order_id}'


class ComponentType(models.TextChoices):
    """Choices of component type for the [opal.pharmacy.models.PharmacyComponent][] model."""

    ADDITIVE = 'A', _('Additive')
    BASE = 'B', _('Base')
    TEXT = 'T', _('Text')


class PharmacyComponent(models.Model):
    """Special instructions or compound specifications to produce a requested prescription/order.

    Pharmacy Component specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXC
    """

    pharmacy_encoded_order = models.ForeignKey('PharmacyEncodedOrder', on_delete=models.CASCADE)
    component_type = models.CharField(max_length=1, choices=ComponentType.choices)
    component_code = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_component_component_code',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    component_amount = models.DecimalField(max_digits=8, decimal_places=3)
    component_units = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_component_component_units',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _('Pharmacy Component')
        verbose_name_plural = _('Pharmacy Components')

    def __str__(self):
        """Provide string representation.

        Returns:
            string representation
        """
        return f'{self.get_component_type_display()} Component for Order {self.pharmacy_encoded_order.id}'
