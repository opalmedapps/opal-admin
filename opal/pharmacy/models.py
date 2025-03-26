"""Module providing models for pharmacy data."""
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.patients.models import Patient


class AbstractQuantityTiming(models.Model):
    """Describes the quantity and timing information for a given prescription/order.

    Quantity/Timing specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Fields/ORC.7

    The default duration is indefinite which can also be taken to mean "until the prescription runs out".
    The default priority is Routine/Default: https://hl7-definition.caristix.com/v2/HL7v2.3/Fields/ORC.7.6
    """

    quantity = models.DecimalField(max_digits=8, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)
    interval_pattern = models.CharField(max_length=100)
    interval_duration = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=50, default='INDEF')
    service_start = models.DateTimeField(blank=True)
    service_end = models.DateTimeField(blank=True)
    priority = models.CharField(max_length=8, default='R')

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
    visit_number = models.IntegerField()
    trigger_event = models.CharField(max_length=2)
    filler_order_number = models.IntegerField()
    order_status = models.CharField(max_length=2, default='SC')
    entered_at = models.DateTimeField()
    entered_by = models.CharField(max_length=80)
    verified_by = models.CharField(max_length=80)
    ordered_by = models.CharField(max_length=80)
    effective_at = models.DateTimeField()

    class Meta:
        verbose_name = _('Physician Prescription')
        verbose_name_plural = _('Physician Prescriptions')

    def __str__(self) -> str:
        """Instance of a physician's order for a patient.

        Returns:
            string representation
        """
        return f'Filler number {self.filler_order_number}, {self.ordered_by} order for {self.patient}'


class FormularyStatus(models.TextChoices):
    """Choices of formulary status type for the PharmacyEncodedOrder model."""

    STANDARD = 'STD', _('Standard')
    AMBULATORY = 'AMB', _('Ambulatory')
    LEAVE = 'LOA', _('Leave Of Absence')
    TAKEHOME = 'TH', _('Take Home')
    SELF = 'SELF', _('Self Administration')  # noqa: WPS117


class PharmacyEncodedOrder(AbstractQuantityTiming):
    """Describes the final prescription/order after any alterations mandated by the pharmacy provider.

    Pharmacy Encoded Order specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXE
    """

    physician_prescription_order = models.OneToOneField(
        'PhysicianPrescriptionOrder',
        on_delete=models.CASCADE,
        related_name='pharmacy_encoded_order',
    )
    give_code = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_give_codes',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    give_amount_maximum = models.DecimalField(null=True, blank=True, max_digits=8, decimal_places=3)
    give_amount_minimum = models.DecimalField(max_digits=8, decimal_places=3)
    give_units = models.CharField(max_length=25, blank=True)
    give_dosage_form = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_encoded_order_give_dosage_forms',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    provider_administration_instruction = models.CharField(max_length=250, blank=True)
    dispense_amount = models.DecimalField(max_digits=8, decimal_places=3)
    dispense_units = models.CharField(max_length=25, blank=True)
    refills = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)
    formulary_status = models.CharField(max_length=4, choices=FormularyStatus.choices)

    class Meta:
        verbose_name = _('Pharmacy Encoding')
        verbose_name_plural = _('Pharmacy Encodings')

    def __str__(self) -> str:
        """Instance of pharmacy encoding of a physician's original order.

        Returns:
            string representation
        """
        return f'Pharmacy encoded prescription of filler order {self.physician_prescription_order.filler_order_number}'


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
        unique_together = (('identifier', 'text', 'coding_system'),)

    def __str__(self) -> str:
        """Instance of the unique identifiers for a coded element.

        Returns:
            string representation
        """
        return f'{self.text} ({self.identifier} - {self.coding_system})'


class PharmacyRoute(models.Model):
    """Special pharmacy-provided instructions for the method of delivery of a prescription/order.

    Pharmacy Route specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXR
    """

    pharmacy_encoded_order = models.ForeignKey(
        'PharmacyEncodedOrder',
        on_delete=models.CASCADE,
        related_name='pharmacy_route',
    )
    route = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_route_route',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    site = models.CharField(max_length=50, blank=True)
    administration_device = models.CharField(max_length=50, blank=True)
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

    def __str__(self) -> str:
        """Instance of a pharmacy route id.

        Returns:
            string representation
        """
        return f'Route for filler order {self.pharmacy_encoded_order.physician_prescription_order.filler_order_number}'


class ComponentType(models.TextChoices):
    """Choices of component type for the PharmacyComponent model."""

    ADDITIVE = 'A', _('Additive')
    BASE = 'B', _('Base')
    TEXT = 'T', _('Text')


class PharmacyComponent(models.Model):
    """Special instructions or compound specifications to produce a requested prescription/order.

    Pharmacy Component specifications: https://hl7-definition.caristix.com/v2/HL7v2.3/Segments/RXC
    """

    pharmacy_encoded_order = models.ForeignKey(
        'PharmacyEncodedOrder',
        on_delete=models.CASCADE,
        related_name='pharmacy_components',
    )
    component_type = models.CharField(max_length=1, choices=ComponentType.choices)
    component_code = models.ForeignKey(
        'CodedElement',
        related_name='pharmacy_component_component_code',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    component_amount = models.DecimalField(max_digits=8, decimal_places=3)
    component_units = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name = _('Pharmacy Component')
        verbose_name_plural = _('Pharmacy Components')

    def __str__(self) -> str:
        """Instance of a pharmacy component type and id.

        Returns:
            string representation
        """
        return 'Component for filler order {0}'.format(
            self.pharmacy_encoded_order.physician_prescription_order.filler_order_number,
        )
