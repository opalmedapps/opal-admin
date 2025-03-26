import requests
from django.conf import settings


def find_patient_by_mrn(mrn: str, site: str):
    url = settings.OIE_HOST
    data = {
        'mrn': mrn,
        'site': site,
        'visitInfo': False,
    }
    response = requests.post(url, data=data)
    return response


def find_patient_by_ramq(ramq: str):
    url = settings.OIE_HOST
    data = {
        'medicareNumber': ramq,
        'visitInfo': False,
    }
    response = requests.post(url, data=data)
    return response
