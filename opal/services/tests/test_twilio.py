from unittest.mock import patch

import pytest
from pytest_django.asserts import assertRaisesMessage
from pytest_django.fixtures import SettingsWrapper
from twilio.rest import Client
from twilio.rest.api import MessageList

from opal.services.twilio import TwilioService, TwilioServiceException

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


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
    def test_send_sms_successfully(self, settings: SettingsWrapper) -> None:
        """Ensure sending sms successfully."""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_ = settings.TWILIO_FROM
        to = '+15146661234'
        message = 'Test sending SMS'
        service = TwilioService(
            account_sid,
            auth_token,
            from_,
        )

        service.client = Client()
        service.send_sms(
            to,
            message,
        )

        assert self.response == {
            'to': to,
            'from_': settings.TWILIO_FROM,
            'body': message,
        }

    @patch.object(MessageList, 'create', create)
    def test_send_sms_exception(self, settings: SettingsWrapper) -> None:
        """Ensure we catch and handle the TwilioException correctly."""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_ = settings.TWILIO_FROM
        to = ''
        message = 'Test sending SMS'
        service = TwilioService(
            account_sid,
            auth_token,
            from_,
        )

        with assertRaisesMessage(TwilioServiceException, 'Sending SMS failed'):
            service.send_sms(
                to,
                message,
            )
