from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.patients.models import Relationship, Patient


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ['id', 'ramq']


class RelationshipSerializer(serializers.ModelSerializer):

    patient = PatientSerializer()

    class Meta:
        model = Relationship
        fields = ['status', 'patient']


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):

    relationship = RelationshipSerializer()

    class Meta:
        model = RegistrationCode
        fields = ['code', 'relationship']
