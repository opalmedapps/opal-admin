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
        Handle GET requests from `api/languages`.

        Args:
            request: Http request.

        Returns:
            Http response with the data needed to return the languages.
        """
        data = []
        languages = settings.LANGUAGES
        for language in languages:
            data.append({
                'code': language[0],
                'name': language[1],
            })
        response = LanguagesSerializer(data, many=True).data
        return Response(response)
