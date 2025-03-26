"""This module provides `ViewSets` for the hospital-specific settings REST API."""
from typing import Type
from uuid import UUID

from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import SecurityAnswer, SecurityQuestion
from . import serializers


class SecurityQuestionViewSet(ListModelMixin, viewsets.GenericViewSet):
    """
    This viewset provides an list model view for `SecurityQuestion`.

    It uses the `SecurityQuestionSerializer` to serialize a `SecurityQuestion`.
    It allows to filter by SecurityQuestion 'title'.
    """

    queryset = SecurityQuestion.objects.filter(is_active=True).order_by('pk')
    serializer_class = serializers.SecurityQuestionSerializer
    filterset_fields = ['title']
    permission_classes = [IsAuthenticated]


class SecurityAnswerViewSet(  # noqa: WPS215
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):  # noqa: WPS215
    """
    This viewset provides an retrieve view and update view for `SecurityAnswer`.

    It uses the `SecurityAnswerSerializer` to serialize a `SecurityAnswer`.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[SecurityAnswer]:
        """
        Override get_queryset to filter security answers by caregiver uuid.

        Returns:
            The queryset of SecurityAnswer
        """
        uuid = self.kwargs['uuid']
        return SecurityAnswer.objects.filter(user__uuid=uuid).order_by('pk')

    def get_serializer_class(self) -> Type[drf_serializers.BaseSerializer]:
        """
        Override get_serializer_class to switch the serializer by the action.

        Returns:
            The expected serializer
        """
        if self.action == 'update':
            return serializers.SecurityAnswerSerializer
        return serializers.SecurityAnswerQuestionSerializer

    @action(detail=False, methods=['get'])
    def random(self, request: Request, uuid: UUID) -> Response:  # noqa: WPS210
        """
        Handle GET requests for a random pair of security question and answer.

        Args:
            request: Http request.
            uuid: uuid of caregiver profile

        Returns:
            Http response with the data needed to return a random pair of security question and answer.
        """
        answer_queryset = self.get_queryset().order_by('?').first()
        serializer = self.get_serializer(answer_queryset)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def verify_answer(self, request: Request, uuid: UUID, pk: int) -> Response:  # noqa: WPS210
        """
        Handle POST requests for verifyig a security answer and a question.

        Args:
            pk: the id of a security question
            uuid: uuid of caregiver profile
            request: Http request.

        Raises:
            ValidationError: the answer is not equal to the correct one.

        Returns:
            Http response with the data needed to
            return the security question when verification succeed,
            return message 'Wrong Answer' when the answer not correct,
            return message 'Wrong Answer' when there is an exception.
        """
        input_serializer = serializers.VerifySecurityAnswerSerializer(data=request.data, partial=True)
        input_serializer.is_valid(raise_exception=True)
        answer = input_serializer.validated_data['answer']
        answer_object = self.get_object()

        answer_value = answer_object.answer
        if answer_value != answer:
            raise drf_serializers.ValidationError(_('The provided answer is not correct'))

        return Response()
