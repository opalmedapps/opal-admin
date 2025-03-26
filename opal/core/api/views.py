"""Module providing reusable views for the whole project."""

from typing import Any, TypeVar

from django.conf import settings
from django.db.models import Model
from django.http import HttpRequest

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_parsers.hl7_parser import HL7Parser
from opal.core.drf_permissions import IsRegistrationListener

from .serializers import LanguageSerializer

_Model = TypeVar('_Model', bound=Model)


class LanguagesView(APIView):
    """View that returns the list of supported languages."""

    permission_classes = (IsRegistrationListener,)

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


class HL7CreateView(CreateAPIView[_Model]):
    """APIView Superclass for all endpoints requiring HL7 parsing."""

    parser_classes = (HL7Parser,)

    def get_parser_context(self, http_request: HttpRequest) -> dict[str, Any]:
        """Append a list of HL7 segments to be parsed to the dictionary of parser context data.

        Each view can define segments_to_parse if desired to add specific segments to parse.

        Args:
            http_request: The incoming request

        Returns:
            parser context for the HL7Parser.parse() method
        """
        context = super().get_parser_context(http_request)
        context['segments_to_parse'] = getattr(self, 'segments_to_parse', None)
        return context
