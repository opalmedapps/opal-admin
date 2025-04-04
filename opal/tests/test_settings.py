# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest_django.fixtures import SettingsWrapper


def test_fedauth_backend_disabled(settings: SettingsWrapper) -> None:
    """The fed auth backend is disabled by default."""
    assert 'opal.core.auth.FedAuthBackend' not in settings.AUTHENTICATION_BACKENDS
