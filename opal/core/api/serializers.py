"""Collection of serializers for the core ApiViews."""
from rest_framework import serializers


class LanguagesSerializer(serializers.Serializer):
    """Serializer for the settings languages."""

    code = serializers.CharField(min_length=2, max_length=2)
    name = serializers.CharField()
