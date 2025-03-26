from unittest.mock import patch

import pytest
from twilio.rest.api import MessageList

from opal.services.twilio import TwilioService, TwilioServiceException


class TestTwilioService:
    """Test class for TwilioService."""

    response = None

    def create(self, to: str, from_: str, body: str) -> None:
        """Mockup Twilio Api MessageList method 'create'.

        Args:  # noqa: RST306
            to: target phone number
            from_: sender phone number
            body: message content

        Raises:
            TwilioServiceException: if 'to' is invalid
        """
        if to == '':
            raise TwilioServiceException('Sending SMS failed')
        TestTwilioService.response = {
            'to': to,
            'from_': from_,
            'body': body,
        }

    @patch.object(MessageList, 'create', create)
    def test_send_sms_successfully(self) -> None:
        """Ensure sending sms successfully."""
        account_sid = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        auth_token = str('your_auth_token')
        from_ = '+15146661234'
        to = '+15145551234'
        message = 'Test sending SMS'
        service = TwilioService(
            account_sid,
            auth_token,
            from_,
        )

        service.send_sms(
            to,
            message,
        )

        assert self.response == {
            'to': to,
            'from_': from_,
            'body': message,
        }

    @patch.object(MessageList, 'create', create)
    def test_send_sms_exception(self) -> None:
        """Ensure we catch and handle the TwilioException correctly."""
        account_sid = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        auth_token = str('your_auth_token')
        from_ = '+15146661234'
        to = ''
        message = 'Test sending SMS'
        service = TwilioService(
            account_sid,
            auth_token,
            from_,
        )

        with pytest.raises(TwilioServiceException) as ex:
            service.send_sms(
                to,
                message,
            )
        assert str(ex.value) == 'Sending SMS failed'  # noqa: WPS441
