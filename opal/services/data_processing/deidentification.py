"""Module providing algorithms and functions related to the de-identification of patient data."""
import hashlib
import logging
import re
from typing import Final

from unidecode import unidecode

from opal.patients.models import SexType

LOGGER = logging.getLogger(__name__)


class OpenScienceIdentity():  # noqa: WPS230
    """This algorithm is used to de-identify patient data using an open source algorithm developed at the McGill Neuro.

    A unique signature is generated for a patient by taking several personal identifiers
    and feeding them into a one way hash. This allows each ID to be unique to a subject while
    also allowing other organizations to arrive at the same signature for a particular patient,
    ensuring proper data ownership per patient.

    OSI Git: https://github.com/aces/open_science_identity/tree/master
    """

    pbkdf2_iterations: Final[int] = 10000
    pbkdf2_hash_function: Final[str] = 'sha256'
    pbkdf2_key_length: Final[int] = 32
    gender_values = [value.lower() for value in SexType.labels]
    identity_attributes = ['first_name', 'last_name', 'gender', 'date_of_birth', 'city_of_birth']

    # Validate dates of YYYY-MM-DD format for 1900s and 2000s birthdates
    dob_regex = r'^(19|20)\d\d-(0[1-9]|1[012])-(0[1-9]|[12]\d|3[01])$'

    def __init__(self, attributes: dict) -> None:
        """Initialize hash password attributes and convenience class data structures.

        Args:
            attributes: dictionary of input arguments to algorithm
        """
        self.gender = attributes.get('gender', '')
        self.first_name = attributes.get('first_name', '')
        self.middle_name = attributes.get('middle_name', '')
        self.last_name = attributes.get('last_name', '')
        self.date_of_birth = attributes.get('date_of_birth', '')
        self.city_of_birth = attributes.get('city_of_birth', '')
        self._cache: dict[str, str] = {}  # Keep a dictionary of cleaned attributes for efficiency
        self.invalid_attributes: list = []  # Easier debugging by tracking invalid inputs

    def to_signature(self) -> str:
        """Validate input attributes, generate the signature (password), and produce the hash.

        Returns:
            The hex representation of hashlib's pbkdf2 derivation
        """
        self._validate()
        sig_key = self._signature_key()
        LOGGER.info('All attributes successfully cleaned & validated')
        salt = sig_key[::-1]
        return hashlib.pbkdf2_hmac(
            self.pbkdf2_hash_function,
            sig_key.encode(),
            salt.encode(),
            self.pbkdf2_iterations,
            self.pbkdf2_key_length,
        ).hex()

    def _clean_attribute(self, attr_name: str) -> str:
        """Generalized cleaning method for any attribute.

        Args:
            attr_name: Name of the attribute to clean.

        Returns:
            Cleaned string.
        """
        if attr_name not in self._cache:
            attr_value = getattr(self, attr_name, '')
            # Cache the result to avoid needing to re-clean data during algorithm execution
            self._cache[attr_name] = self._plain_alpha(attr_value)
        return self._cache[attr_name]

    def _plain_alpha(self, string: str) -> str:
        """Clean the input string by lowercasing, transliterating, and filtering by alphanumerics.

        The goal of transliterating is to unify special Unicode characters
        with their nearest 'normal' ASCII representation.
        So for example, an input string `Côté-LeBœuf` should become `coteleboeuf` after cleaning.

        Args:
            string: candidate string to be cleaned

        Returns:
            Cleaned string, or empty string
        """
        if not string or string.strip() == '':
            return ''

        # Transliterate the string to its closest ASCII representation
        transliterated_string = unidecode(string)

        return ''.join(char.lower() for char in transliterated_string if char.isalnum())

    def _valid(self) -> bool:
        """Implement the validity functions for each class attribute.

        Returns:
            boolean whether all identity attributes are valid.
        """
        for attr in self.identity_attributes:
            cleaned_value = self._clean_attribute(attr)
            if not cleaned_value or (attr == 'gender' and cleaned_value not in self.gender_values):
                self.invalid_attributes.append(attr)

        if self.date_of_birth and not re.match(self.dob_regex, self.date_of_birth):
            self.invalid_attributes.append('date_of_birth')

        return not self.invalid_attributes

    def _validate(self) -> None:
        """Check for identity attribute validity and raise error if not valid.

        Raises:
            ValueError: if any identify attributes are missing or otherwise invalid.
        """
        if not self._valid():
            raise ValueError(f"Invalid identity components {', '.join(self.invalid_attributes)}")

    def _signature_key(self) -> str:
        """Generate the password for the pbfkd2 function from the cleaned attributes.

        Example:
             male|pierre|tiberius|rioux|19211231|newyorkcity

        Returns:
            bar separated password string
        """
        components = [
            self._clean_attribute('gender'),
            self._clean_attribute('first_name'),
            self._clean_attribute('middle_name'),
            self._clean_attribute('last_name'),
            self._clean_attribute('date_of_birth'),
            self._clean_attribute('city_of_birth'),
        ]
        return '|'.join(components)
