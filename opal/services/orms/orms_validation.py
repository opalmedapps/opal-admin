"""Module providing validation rules for the data being sent/received to/from ORMS."""
from typing import Any


class ORMSValidator:
    """ORMS helper service that validates ORMS request and response data."""

    # TODO Raise exceptions instead of returning them in an array.
    #   Also adjust `initialize_new_opal_patient` accordingly;
    #   its calls to ORMS, the source system etc. should be handled and
    #   not cause the whole function to fail.
    # TODO log or return original errors from ORMS instead of suppressing them
    def is_patient_response_valid(
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
        status = response_data.get('status')
        success = status == 'Success'

        if status is None:
            errors.append('Patient response data does not have the attribute "status"')
        elif status == 'Error':
            errors.append('Error response from ORMS')

            # Specific case for the patient not being found
            if response_data.get('error') == 'Patient not found':
                errors.append('Skipping patient initialization in ORMS because the patient was not found there')
        elif not success:
            errors.append(f'Patient response data has an unexpected "status" value: {status}')

        return success, errors
