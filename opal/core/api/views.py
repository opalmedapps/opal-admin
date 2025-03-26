"""Module providing reusable views for the whole project."""

from django.conf import settings
from django.http import HttpRequest

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LanguageSerializer


class LanguagesView(APIView):
    """View that returns the list of supported languages."""

    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> Response:
        """
        Handle GET requests to list the supported languages.

        Args:
            request: the HTTP request

        Returns:
            HTTP response with a list of languages
        """
        data = [{'code': code, 'name': name} for (code, name) in settings.LANGUAGES]
        response = LanguageSerializer(data, many=True).data
        return Response(response)
