from http import HTTPStatus

import pytest
from pytest_mock import MockerFixture
from twilio.base.exceptions import TwilioRestException
from twilio.rest.api import MessageList

from opal.services.twilio import TwilioService, TwilioServiceException


class TestTwilioService:
    """Test class for TwilioService."""

    sender = '15141234567'
    service = TwilioService('account_sid', 'auth_token', sender)

    def test_send_sms_successfully(self, mocker: MockerFixture) -> None:
        """Ensure sending sms successfully."""
        mock_create = mocker.patch.object(MessageList, 'create')

        to = '+15145551234'
        message = 'Test sending SMS'

        self.service.send_sms(
            to,
            message,
        )

        mock_create.assert_called_once_with(to=to, from_=self.sender, body=message)

    def test_send_sms_exception(self, mocker: MockerFixture) -> None:
        """Ensure we catch and handle the TwilioException correctly."""
        mock_create = mocker.patch.object(MessageList, 'create')
        mock_create.side_effect = TwilioRestException(HTTPStatus.FORBIDDEN, 'uri', 'an error occurred')

        to = ''
        message = 'Test sending SMS'

        with pytest.raises(TwilioServiceException) as exc:
            self.service.send_sms(
                to,
                message,
            )

        assert str(exc.value) == 'HTTP 403 error: Sending SMS failed'
        assert exc.value.__cause__.status == HTTPStatus.FORBIDDEN
