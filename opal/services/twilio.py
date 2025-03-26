"""Sending SMS service, working with twilio."""
from twilio.base.exceptions import TwilioException, TwilioRestException
from twilio.rest import Client


class TwilioServiceError(Exception):
    """An error occurred while sending an SMS via Twilio."""


class TwilioService:
    """This service send SMS to the users via twilio."""

    def __init__(self, account_sid: str, auth_token: str, sender: str) -> None:
        """
        Initialize the Twilio service with the given credentials.

        Args:
            account_sid: twilio account sid
            auth_token: twilio auth token
            sender: sender phone number

        Raises:
            TwilioException: if the twilio service could not be initialized.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_ = sender
        try:
            self.client = Client(account_sid, auth_token)
        except TwilioException as exp:
            raise TwilioException(
                'The Twilio Service could not be initialized:/n{0}'.format(str(exp)),
            )

    def send_sms(self, phone_number: str, message: str) -> None:
        """
        Send a message to the phone number.

        Args:
            phone_number: phone number to send the SMS to
            message: the message to send

        Raises:
            TwilioServiceError: if there is an error sending the SMS
        """
        try:
            self.client.messages.create(
                to=phone_number,
                from_=self.from_,
                body=message,
            )
        except TwilioRestException as exc:
            raise TwilioServiceError('Sending SMS failed') from exc
