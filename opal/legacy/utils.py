"""Utility functions used by legacy API views."""

from .models import LegacyUsers


def get_patient_sernum(username: str) -> int:
    """
    Get the patient sernum associated with the username to query the legacy database.

    Args:
        username: Firebase username making the request

    Returns:
        User patient sernum associated with the request username user name.
    """
    user = LegacyUsers.objects.filter(
        username=username,
        usertype='Patient',
    ).first()
    if user:
        return user.usertypesernum
    return 0
