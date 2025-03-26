
import pytest

from opal.core.test_utils import CommandTestMixin

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestDailyUsageStatisticsUpdate(CommandTestMixin):
    """Test class to group the `update_daily_usage_statistics` command tests."""

    def test_no_user_app_statistics(self) -> None:
        """Ensure that the command does not fail when there is no user app statistics."""
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated statistics data to DailyUserAppActivity model\n'
