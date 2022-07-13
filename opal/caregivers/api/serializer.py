from rest_framework import serializers

from opal.caregivers.models import RegistrationCode


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationCode
        fields = ['code', 'relationship']
