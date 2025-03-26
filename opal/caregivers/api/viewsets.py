"""This module provides `ViewSets` for the hospital-specific settings REST API."""
from http import HTTPStatus

from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from opal.caregivers.api.serializer import SecurityQuestionSerializer
from opal.caregivers.models import SecurityAnswer, SecurityQuestion


class SecurityQuestionViewSet(viewsets.ModelViewSet):
    """
    This viewset provides an API view for `SecurityQuestion`.

    It uses the `SecurityQuestionSerializer` to serialize a `SecurityQuestion`.
    It allows to filter by SecurityQuestion `id`, 'title' and 'is_active'.
    """

    queryset = SecurityQuestion.objects.all()
    serializer_class = SecurityQuestionSerializer
    filterset_fields = ['id', 'title', 'is_active']
    permission_classes = [IsAuthenticated]

    def get_all_active(self, request: Request) -> Response:
        """
        Handle GET requests for active security questions.

        Args:
            request: Http request.

        Returns:
            Http response with the data needed to return the active security questions.
        """
        queryset = self.queryset.filter(is_active=True)
        serializer = self.serializer_class(queryset, many=True, read_only=True)
        return Response(serializer.data)

    def update_question(self, request: Request) -> Response:
        """
        Handle PUT requests for updating a security question.

        Args:
            request: Http request.

        Returns:
            Http response with the data needed to return the updated security question.
        """
        serializer = self.get_serializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exce:
            error = exce.args[0]
            return Response(error, status=HTTPStatus.CREATED)

        exists = SecurityQuestion.objects.get(title_en=request.data.get('title_en'))
        serializer.update(exists, request.data)
        return Response(serializer.data)

    def get_random_question(self, request: Request) -> Response:
        """
        Handle GET requests for a random security question.

        Args:
            request: Http request.

        Returns:
            Http response with the data needed to return a random security question.
        """
        queryset = SecurityQuestion.objects.order_by('?').first()
        serializer = self.serializer_class(queryset, partial=True, read_only=True)
        return Response(serializer.data)

    def verify_answer(self, request: Request, question_id: int) -> Response:  # noqa: WPS210
        """
        Handle POST requests for verifyig a security answer and a question.

        Args:
            question_id: the id of a security question
            request: Http request.

        Returns:
            Http response with the data needed to
            return the security question when verification succeed,
            return message 'Wrong Answer' when the answer not correct,
            return message 'Wrong Answer' when there is an exception.
        """
        answer = request.data.get('answer')
        queryset = SecurityQuestion.objects.get(id=question_id)
        serializer = self.serializer_class(queryset, partial=True, read_only=True)
        question = serializer.data['title']

        try:
            answer_object = SecurityAnswer.objects.get(question=question)
        except ObjectDoesNotExist:
            return Response(
                {'detail': 'Wrong Answer'},
                status=HTTPStatus.NOT_FOUND,
            )

        answer_value = answer_object.answer
        if answer_value != answer:
            return Response(
                {'detail': 'Wrong Answer'},
                status=HTTPStatus.NOT_FOUND,
            )

        return Response(serializer.data)
