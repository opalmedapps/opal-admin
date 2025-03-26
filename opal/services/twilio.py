"""Sending SMS service, working with twilio."""
from twilio.base.exceptions import TwilioException
from twilio.rest import Client


class TwilioServiceException(TwilioException):
    """This Exception class for TwilioService."""


class TwilioService:
    """This serice send SMS to the users via twilio."""

    def __init__(self, account_sid: str, auth_token: str, _from: str) -> None:
        """
        Initialize the twilio credential.

        Args:
            account_sid: twilio account sid
            auth_token: twilio auth token
            _from: sender phone number
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_ = _from
        self.client = Client()

    def send_sms(self, phone_number: str, message: str) -> None:
        """
        Send message to the phone number.

        Args:
            phone_number: user phone number
            message: message sent to the user

        Raises:
            TwilioServiceException: if there is a TwilioException
        """
        try:
            self.client.messages.create(
                to=phone_number,
                from_=self.from_,
                body=message,
            )
        except TwilioException:
            raise TwilioServiceException('Sending SMS failed')
