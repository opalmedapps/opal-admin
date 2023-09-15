"""Module providing validation rules for the data being sent/received to/from ORMS."""
from typing import Any


class ORMSValidator:
    """ORMS helper service that validates ORMS request and response data."""

    def is_patient_response_valid(  # noqa: C901, WPS231
        self,
        response_data: Any,
    ) -> tuple[bool, list[str]]:
        """Check if the ORMS patient response data is valid.

        Args:
            response_data (Any): ORMS patient response data received from ORMS

        return:
            return a boolean indicating validity (true if valid, false otherwise) and an errors list
        """
        errors = []
        status = ''
        success = False
        try:
            status = response_data['status']
        except KeyError:
            errors.append('Patient response data does not have the attribute "status"')

        if not errors and status == 'Success':
            success = True
        elif status == 'Error':
            errors.append('Error response from ORMS')

            # Specific case for the patient not being found
            try:
                if response_data['error'] == "Patient not found":
                    errors.append('Skipping patient initialization in ORMS because the patient was not found there')
            except KeyError:
                pass
        else:
            errors.append('Patient response data is in an unexpected format')

        return success, errors
