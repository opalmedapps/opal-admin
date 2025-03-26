from datetime import date, datetime

from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData

from .. import validators

CUSTOMIZED_OIE_PATIENT_DATA = OIEPatientData(
    date_of_birth=date.fromisoformat('1984-05-09'),
    first_name='Marge',
    last_name='Simpson',
    sex='F',
    alias='',
    deceased=False,
    death_date_time=datetime.strptime('2054-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
    ramq='MARG99991313',
    ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
    mrns=[
        OIEMRNData(
            site='MGH',
            mrn='9999993',
            active=True,
        ),
        OIEMRNData(
            site='MCH',
            mrn='9999994',
            active=True,
        ),
        OIEMRNData(
            site='RVH',
            mrn='9999993',
            active=True,
        ),
    ],
)


def test_some_mrns_have_same_site_code() -> None:
    """Test some MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999994',
                active=False,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_all_mrns_have_same_site_code() -> None:
    """Test all MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=False,
            ),
        ],
    )
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_no_mrns_have_same_site_code() -> None:
    """Test No MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MCH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is False
