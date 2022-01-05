from rest_framework import serializers

from .models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ['url', 'name', 'code', 'parking_url']


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = ['url', 'name', 'code', 'parking_url', 'sites']
