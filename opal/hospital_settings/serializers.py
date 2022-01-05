from rest_framework import serializers

from .models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ['url', 'parking_url', 'name', 'code']


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = ['url', 'parking_url', 'name', 'code', 'sites']
