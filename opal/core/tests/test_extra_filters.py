import pytest

from ..templatetags import extra_filters as filters


@pytest.mark.parametrize(('text', 'prefix', 'expected'), [
    ('test', 'test', True),
    ('test', 't', True),
    ('test', 's', False),
])
def test_startswith(text: str, prefix: str, expected: bool) -> None:
    """Ensure the startswith filter detects the prefix correctly."""
    assert filters.startswith(text, prefix) == expected


@pytest.mark.parametrize(('text', 'separator', 'expected'), [
    ('foobar', 'b', 'foo'),
    ('foobar', 'x', ''),
    ('hospital-settings:institution-list', '-', 'hospital-settings:institution'),
])
def test_rsubstring(text: str, separator: str, expected: str) -> None:
    """Ensure the rsubstring filter returns the correct result."""
    assert filters.rsubstring(text, separator) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('bar', 'bar'),
    (' bar', 'bar'),
    ('bar ', 'bar'),
    ('      \nbar         \n         ', 'bar'),
    ('      \nbar         \n    foo     ', 'bar         \n    foo'),
])
def test_strip(text: str, expected: str) -> None:
    """Ensure the strip filter returns the correct result."""
    assert filters.strip(text) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('bar ', 'bar'),
    ('bar\n', 'bar'),
    (' \nbar', 'bar'),
    ('bar\n \n \n', 'bar'),
    ('bar\n\n\n', 'bar'),
    ('      \nbar         \n         ', 'bar'),
    ('      \nbar         \n    foo     ', 'bar foo'),
])
def test_striplines(text: str, expected: str) -> None:
    """Ensure the striplines filter returns the correct result."""
    assert filters.striplines(text) == expected
