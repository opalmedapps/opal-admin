"""This module provides Django REST framework serializers related to the `test_results` app's models."""

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.api.serializers import HospitalPatientSerializer
from opal.test_results.models import GeneralTest, Note, Observation


class GeneralTestSerializer(DynamicFieldsSerializer):
    """Serializer for the `GeneralTest` (a.k.a. pathology) info received from the `pathology create` endpoint."""

    mrns = HospitalPatientSerializer(many=True, allow_empty=False, required=True)

    class Meta:
        model = GeneralTest
        fields = [
            'type',
        ]
