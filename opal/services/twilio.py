"""Sending SMS service, working with Twilio."""
from twilio.base.exceptions import TwilioException
from twilio.rest import Client


class TwilioServiceError(Exception):
    """An error occurred while sending an SMS via Twilio."""


class TwilioService:
    """This service send SMS to the users via Twilio."""

    def __init__(self, account_sid: str, auth_token: str, sender: str) -> None:
        """
        Initialize the Twilio service with the given credentials.

        Args:
            account_sid: Twilio account sid
            auth_token: Twilio auth token
            sender: sender phone number
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_ = sender

    def send_sms(self, phone_number: str, message: str) -> None:
        """
        Send a message to the phone number.

        Args:
            phone_number: phone number to send the SMS to
            message: the message to send

        Raises:
            TwilioServiceError: if there is an error sending the SMS
        """
        try:  # noqa: WPS229 (much easier to deal with one try-except block here)
            # can raise a TwilioException if the credentials are empty strings
            # NOTE: if ever this module gets bigger,
            # consider adding a Django check to ensure that the credential is not falsy during startup
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(
                to=phone_number,
                from_=self.from_,
                body=message,
            )
        except TwilioException as exc:
            raise TwilioServiceError('Sending SMS failed') from exc
