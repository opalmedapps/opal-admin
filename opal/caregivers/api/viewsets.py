"""This module provides `ViewSets` for the hospital-specific settings REST API."""
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response

from opal.core.drf_permissions import FullDjangoModelPermissions, IsListener

from ..models import SecurityAnswer, SecurityQuestion
from . import serializers


class SecurityQuestionViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet[SecurityQuestion]):
    """
    This viewset provides a list and retrieve actions for the  `SecurityQuestion` model.

    It uses the `SecurityQuestionSerializer` to serialize a `SecurityQuestion`.
    It allows to filter by SecurityQuestion 'title'.
    """

    queryset = SecurityQuestion.objects.filter(is_active=True).order_by('pk')
    serializer_class = serializers.SecurityQuestionSerializer
    filterset_fields = ['title']
    permission_classes = (FullDjangoModelPermissions,)


class SecurityAnswerViewSet(  # noqa: WPS215
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet[SecurityAnswer],
):  # noqa: WPS215
    """
    This viewset provides an retrieve view and update view for `SecurityAnswer`.

    It uses the `SecurityAnswerSerializer` to serialize a `SecurityAnswer`.
    """

    permission_classes = (IsListener,)
    queryset = SecurityAnswer.objects.none()

    def get_queryset(self) -> QuerySet[SecurityAnswer]:  # noqa: WPS615
        """
        Override get_queryset to filter security answers by caregiver uuid.

        Returns:
            The queryset of SecurityAnswer
        """
        username = self.kwargs['username']
        return SecurityAnswer.objects.filter(user__user__username=username).order_by('pk')

    def get_serializer_class(self) -> type[drf_serializers.BaseSerializer[SecurityAnswer]]:
        """
        Override get_serializer_class to switch the serializer by the action.

        Returns:
            The expected serializer
        """
        if self.action == 'update':
            return serializers.SecurityAnswerSerializer
        return serializers.SecurityAnswerQuestionSerializer

    @action(detail=False, methods=['get'])
    def random(self, request: Request, username: str) -> Response:  # noqa: WPS210
        """
        Handle GET requests for a random pair of security question and answer.

        Security: this endpoint exposes security answers, and should only be called by the listener.
        TODO: Use permissions (e.g. group permissions) to restrict access of this endpoint only to the listener.

        Args:
            request: Http request.
            username: user username

        Returns:
            Http response with the data needed to return a random pair of security question and answer.
        """
        answer_queryset = self.get_queryset().order_by('?').first()
        serializer = serializers.SecurityAnswerSerializer(answer_queryset)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def verify_answer(self, request: Request, username: str, pk: int) -> Response:  # noqa: WPS210
        """
        Handle POST requests for verifyig a security answer and a question.

        Args:
            pk: the id of a security question
            username: user username
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
