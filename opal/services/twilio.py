"""Sending SMS service, working with twilio."""
from twilio.base.exceptions import TwilioException
from twilio.rest import Client


class TwilioServiceException(TwilioException):
    """This Exception class for TwilioService."""


class TwilioService:
    """This serice send SMS to the users via twilio."""

    def __init__(self, account_sid: str, auth_token: str, sender: str) -> None:
        """
        Initialize the twilio credential.

        Args:
            account_sid: twilio account sid
            auth_token: twilio auth token
            sender: sender phone number
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_ = sender
        self.client = Client(account_sid, auth_token)

    def send_sms(self, phone_number: str, message: str) -> None:
        """
        Send a message to the phone number.

        Args:
            phone_number: phone number to send the SMS to
            message: the message to send

        Raises:
            TwilioServiceException: if there is an error sending the SMS
        """
        try:
            self.client.messages.create(
                to=phone_number,
                from_=self.from_,
                body=message,
            )
        except TwilioException as exc:
            raise TwilioServiceException('Sending SMS failed') from exc
