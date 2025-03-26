from http import HTTPStatus

import pytest
from pytest_mock import MockerFixture
from twilio.base.exceptions import TwilioException, TwilioRestException
from twilio.rest.api import MessageList

from opal.services.twilio import TwilioService, TwilioServiceError


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

    def test_send_sms_empty_credentials(self, mocker: MockerFixture) -> None:
        """Ensure we catch the TwilioException when instantiating the client."""
        mocker.patch.object(MessageList, 'create', side_effect=TwilioException('an error occurred'))

        with pytest.raises(TwilioServiceError) as exc:
            self.service.send_sms('', '')

        assert str(exc.value) == 'Sending SMS failed'
        assert isinstance(exc.value.__cause__, TwilioException)
        assert str(exc.value.__cause__) == 'an error occurred'

    def test_send_sms_exception(self, mocker: MockerFixture) -> None:
        """Ensure we catch and handle the TwilioException correctly."""
        mock_create = mocker.patch.object(MessageList, 'create')
        mock_create.side_effect = TwilioRestException(HTTPStatus.FORBIDDEN, 'uri', 'an error occurred')

        to = ''
        message = 'Test sending SMS'

        with pytest.raises(TwilioServiceError) as exc:
            self.service.send_sms(
                to,
                message,
            )

        assert str(exc.value) == 'Sending SMS failed'
        assert isinstance(exc.value.__cause__, TwilioRestException)
        assert exc.value.__cause__.status == HTTPStatus.FORBIDDEN
