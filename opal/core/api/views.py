"""Module providing reusable views for the whole project."""

from django.conf import settings
from django.http import HttpRequest

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LanguagesSerializer


class LanguagesView(APIView):
    """Class to return languages."""

    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> Response:
        """
        Handle GET requests for supported languages.

        Args:
            request: Http request.

        Returns:
            Http response with the data needed to return the languages.
        """
        data = [{'code': code, 'name': name} for (code, name) in settings.LANGUAGES]
        response = LanguagesSerializer(data, many=True).data
        return Response(response)
