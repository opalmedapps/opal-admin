from opal.services.hospital_communication import OIEHTTPCommunicationManager
from opal.services.hospital_error import OIEErrorHandler

communication_manager = OIEHTTPCommunicationManager()


# __init__

def test_init() -> None:
    """Ensuer init function creates error handler (a.k.a., error helper service)."""
    assert isinstance(communication_manager.error_handler, OIEErrorHandler)
    assert communication_manager.error_handler is not None

# submit

# fetch
