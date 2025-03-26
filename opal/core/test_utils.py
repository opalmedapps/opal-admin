"""Utility classes used by management commands or in the testing of management commands."""
from io import StringIO
from typing import Any

from django.core.management import call_command


class CommandTestMixin:
    """Mixin to facilitate testing of management commands."""

    def _call_command(self, command_name: str, *args: Any, **kwargs: Any) -> tuple[str, str]:
        """
        Call a management command and return the command's standard and error output.

        Args:
            command_name: specify the command name to run
            args: non-keyword input parameter
            kwargs: keywords input parameter

        Returns:
            tuple of stdout and stderr output
        """
        out = StringIO()
        err = StringIO()
        call_command(
            command_name,
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()
