"""This module provides Django REST framework serializers for PatietnView api return value."""
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.patients.serializer import HospitalPatientRegistrationSerializer, InstitutionSiteSerializer, PatientRegistrationSerializer


class RegistrationCodePatientSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration code."""
    patient = PatientRegistrationSerializer(source='relationship.patient', many=False, read_only=True)
    institution = InstitutionSiteSerializer(
        source='relationship.patient.hospital_patients.site.institution',
        many=True,
        read_only=True,
    )
    hospital_patients = HospitalPatientRegistrationSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'institution', 'hospital_patients']
