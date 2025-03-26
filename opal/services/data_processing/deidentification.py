"""Module providing algorithms and functions related to the de-identification of patient data."""
import hashlib
import logging
from dataclasses import dataclass
from datetime import date
from typing import Final

from unidecode import unidecode

from opal.patients.models import SexType

LOGGER = logging.getLogger(__name__)


@dataclass
class PatientData:
    """Dataclass instance for patient identifiers."""

    first_name: str
    middle_name: str
    last_name: str
    gender: str
    date_of_birth: str
    city_of_birth: str


class OpenScienceIdentity():
    """This algorithm is used to de-identify patient data using an open source algorithm developed at the McGill Neuro.

    A unique signature is generated for a patient by taking several personal identifiers
    and feeding them into a one way hash. This allows each ID to be unique to a subject while
    also allowing other organizations to arrive at the same signature for a particular patient,
    ensuring proper data ownership per patient.

    OSI Git: https://github.com/aces/open_science_identity/tree/master
    """

    _pbkdf2_iterations: Final[int] = 10000
    _pbkdf2_hash_function: Final[str] = 'sha256'
    _pbkdf2_key_length: Final[int] = 32
    _gender_values = [value.lower() for value in SexType.labels]
    # Identity attributes are the minimum required attributes for GUID generation
    _identity_attributes = ['first_name', 'last_name', 'gender', 'date_of_birth', 'city_of_birth']

    def __init__(self, patient_data: PatientData) -> None:
        """Initialize hash password attributes and convenience class data structures.

        Args:
            patient_data: dictionary of input arguments to algorithm
        """
        self.patient_data = patient_data
        self._cache: dict[str, str] = {}  # Keep a dictionary of cleaned attributes for efficiency
        self.invalid_attributes: list[str] = []  # Easier debugging by tracking invalid inputs

    def to_signature(self) -> str:
        """Validate input attributes, generate the signature (password), and produce the hash.

        Returns:
            The hex representation of hashlib's pbkdf2 derivation
        """
        self._clean_and_validate()
        sig_key = self._signature_key()
        LOGGER.info('All attributes successfully cleaned & validated')
        salt = sig_key[::-1]
        return hashlib.pbkdf2_hmac(
            self._pbkdf2_hash_function,
            sig_key.encode(),
            salt.encode(),
            self._pbkdf2_iterations,
            self._pbkdf2_key_length,
        ).hex()

    def _clean_general_attribute(self, attr_name: str) -> str:
        """Generalized cleaning method for any attribute.

        Args:
            attr_name: Name of the attribute to clean.

        Returns:
            Cleaned string.
        """
        if attr_name not in self._cache:
            attr_value = getattr(self.patient_data, attr_name, '')
            # Cache the result to avoid needing to re-clean data during algorithm execution
            self._cache[attr_name] = self._plain_alpha(attr_value)
        return self._cache[attr_name]

    def _is_valid_date(self) -> None:
        """Implement special cleaning logic for date_of_birth attribute."""
        if self.patient_data.date_of_birth:
            try:
                dob = date.fromisoformat(self.patient_data.date_of_birth)
            except ValueError:
                self.invalid_attributes.append('date_of_birth')
                return
            # Additional check for 'realistic' date_of_birth
            today = date.today()
            if dob.year < 1900 or today.year < dob.year:  # noqa: WPS432
                self.invalid_attributes.append('date_of_birth')

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

    def _clean_and_validate(self) -> None:
        """Implement the validity and cleaning functions for each class attribute.

        Raises:
            ValueError: if any identify attributes are missing or otherwise invalid.
        """
        # General cleaning and validation for all attributes, gender must be in specified list
        for attr in self._identity_attributes:
            cleaned_value = self._clean_general_attribute(attr)
            if not cleaned_value or (attr == 'gender' and cleaned_value not in self._gender_values):
                self.invalid_attributes.append(attr)

        # Special validation rules for date_of_birth
        self._is_valid_date()

        # Raise error if any validation fails
        if self.invalid_attributes:
            raise ValueError(f"Invalid identity components {', '.join(self.invalid_attributes)}")

    def _signature_key(self) -> str:
        """Generate the password for the pbfkd2 function from the cleaned attributes.

        Example:
             male|pierre|tiberius|rioux|19211231|newyorkcity

        Returns:
            bar separated password string
        """
        components = [
            self._clean_general_attribute('gender'),
            self._clean_general_attribute('first_name'),
            self._clean_general_attribute('middle_name'),
            self._clean_general_attribute('last_name'),
            self._clean_general_attribute('date_of_birth'),
            self._clean_general_attribute('city_of_birth'),
        ]
        return '|'.join(components)
