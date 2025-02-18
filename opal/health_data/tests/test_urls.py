# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from uuid import uuid4

from django.urls import resolve, reverse


def test_health_data_ui_url_exists() -> None:
    """A URL for wearables UI page exists."""
    uuid = uuid4()
    url = f'/health-data/{uuid}/quantity-samples/'
    assert reverse('health_data:health-data-ui', kwargs={'uuid': uuid}) == url
    assert resolve(url).view_name == 'health_data:health-data-ui'
