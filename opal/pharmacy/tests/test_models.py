import pytest

from .. import factories

pytestmark = pytest.mark.django_db()


def test_coded_element_factory() -> None:
    """Ensure the `CodedElement` factory creates a valid model."""
    codedelement = factories.CodedElementFactory()
    codedelement.full_clean()


def test_coded_element_str() -> None:
    """Ensure the `CodedElement` str method works as expected."""
    codedelement = factories.CodedElementFactory(
        identifier='APIXA5',
        text='APIXABAN TAB 5 mg',
        coding_system='RXTFC',
    )
    codedelement.full_clean()
    assert str(codedelement) == 'APIXABAN TAB 5 mg (APIXA5 - RXTFC)'


def test_physician_prescription_order_factory() -> None:
    """Ensure the `PhysicianPrescriptionOrder` factory creates a valid model."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory()
    physicianorder.full_clean()


def test_physician_prescription_order_str() -> None:
    """Ensure the `PhysicianPrescriptionOrder` str method works as expected."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory(
        ordered_by='Dr John Doe',
        filler_order_number=25275236,
    )
    physicianorder.full_clean()
    assert str(physicianorder) == 'Filler number 25275236, Dr John Doe order for Simpson, Marge'


def test_pharmacy_encoded_order_factory() -> None:
    """Ensure the `PharmacyEncodedOrder` factory creates a valid model."""
    pharmacyorder = factories.PharmacyEncodedOrderFactory()
    pharmacyorder.full_clean()


def test_pharmacy_encoded_order_str() -> None:
    """Ensure the `PharmacyEncodedOrder` str method works as expected."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory(
        filler_order_number=25275236,
    )
    pharmacyorder = factories.PharmacyEncodedOrderFactory(physician_prescription_order=physicianorder)
    pharmacyorder.full_clean()
    assert str(pharmacyorder) == 'Pharmacy encoded prescription of filler order 25275236'


def test_pharmacy_route_factory() -> None:
    """Ensure the `PharmacyRoute` factory creates a valid model."""
    pharmacyroute = factories.PharmacyRouteFactory()
    pharmacyroute.full_clean()


def test_pharmacy_route_str() -> None:
    """Ensure the `PharmacyRoute` str method works as expected."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory(
        filler_order_number=25275236,
    )
    pharmacyorder = factories.PharmacyEncodedOrderFactory(physician_prescription_order=physicianorder)
    pharmacyroute = factories.PharmacyRouteFactory(pharmacy_encoded_order=pharmacyorder)
    pharmacyroute.full_clean()
    assert str(pharmacyroute) == 'Route for filler order 25275236'


def test_pharmacy_component_factory() -> None:
    """Ensure the `PharmacyComponent` factory creates a valid model."""
    pharmacycomponent = factories.PharmacyComponentFactory()
    pharmacycomponent.full_clean()


def test_pharmacy_component_str() -> None:
    """Ensure the `PharmacyComponent` str method works as expected."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory(
        filler_order_number=25275236,
    )
    pharmacyorder = factories.PharmacyEncodedOrderFactory(physician_prescription_order=physicianorder)
    pharmacycomponent = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    pharmacycomponent.full_clean()
    assert str(pharmacycomponent) == 'Component for filler order 25275236'


def test_multi_observations_test() -> None:
    """Ensure multiple component instances can be assigned to one PharmacyEncodedOrder."""
    pharmacyorder = factories.PharmacyEncodedOrderFactory()
    component1 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component2 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component3 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component4 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component5 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)

    components = [component1, component2, component3, component4, component5]
    for component in components:
        component.full_clean()
