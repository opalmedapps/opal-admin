import pandas as pd
from _pytest.logging import LogCaptureFixture  # noqa: WPS436

from opal.services.charts import ChartData, ChartService

chart_service = ChartService()

CHART_DATA = ChartData(
    title='Test title',
    label_x='Test label x',
    label_y='Test label y',
    label_legend='Test label legend',
    data=pd.DataFrame({}),
)


def test_generate_line_chart_empty() -> None:
    """Ensure generate_line_chart handles empty chart_data.data gracefully."""
    chart = chart_service.generate_line_chart(CHART_DATA)
    assert not chart


def test_generate_line_chart_missing_columns(caplog: LogCaptureFixture) -> None:
    """Ensure generate_line_chart handles missing columns gracefully and logs an error."""
    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'not_x': 10, 'not_y': 20, 'not_legend': 'test legend'},
            {'not_x': 20, 'not_y': 30, 'not_legend': 'test legend'},
            {'not_x': 30, 'not_y': 40, 'not_legend': 'test legend'},
        ),
    )

    error = '{0}\n{1}\n{2} {3}\n\n'.format(
        'An error occurred in ChartService::generate_line_chart(chart_data: ChartData):',
        'chart_data.data should contain the following columns: x, y, legend',
        'The columns received:',
        "Index(['not_x', 'not_y', 'not_legend'], dtype='object')",
    )
    chart = chart_service.generate_line_chart(chart_data)
    assert caplog.records[0].message == error
    assert caplog.records[0].levelname == 'ERROR'
    assert not chart

    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'x': 10, 'y': 20, 'not_legend': 'test legend'},
            {'x': 20, 'y': 30, 'not_legend': 'test legend'},
            {'x': 30, 'y': 40, 'not_legend': 'test legend'},
        ),
    )

    error = '{0}\n{1}\n{2} {3}\n\n'.format(
        'An error occurred in ChartService::generate_line_chart(chart_data: ChartData):',
        'chart_data.data should contain the following columns: x, y, legend',
        'The columns received:',
        "Index(['x', 'y', 'not_legend'], dtype='object')",
    )
    chart = chart_service.generate_line_chart(chart_data)
    assert caplog.records[1].message == error
    assert caplog.records[1].levelname == 'ERROR'

    assert not chart


def test_generate_line_chart_success() -> None:
    """Ensure generate_line_chart successfully produces line charts."""
    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'x': 10, 'y': 20, 'legend': 'test legend'},
            {'x': 20, 'y': 30, 'legend': 'test legend'},
            {'x': 30, 'y': 40, 'legend': 'test legend'},
        ),
    )

    chart = chart_service.generate_line_chart(chart_data)
    assert chart
    assert 'test legend' in chart
    assert 'Test title' in chart
    assert 'Test label x' in chart
    assert 'Test label y' in chart
    assert 'Test label legend' in chart


def test_generate_error_bar_chart_empty() -> None:
    """Ensure generate_error_bar_chart handles empty chart_data.data gracefully."""
    chart = chart_service.generate_error_bar_chart(CHART_DATA)
    assert not chart


def test_generate_error_bar_chart_missing_columns(caplog: LogCaptureFixture) -> None:
    """Ensure generate_error_bar_chart handles missing columns gracefully and logs an error."""
    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'not_x': 10, 'not_error_max': 100, 'not_error_min': 10, 'not_legend': 'test legend'},
            {'not_x': 20, 'not_error_max': 200, 'not_error_min': 20, 'not_legend': 'test legend'},
            {'not_x': 30, 'not_error_max': 300, 'not_error_min': 30, 'not_legend': 'test legend'},
        ),
    )

    error = '{0}\n{1}\n{2} {3}\n\n'.format(
        'An error occurred in ChartService::generate_error_bar_chart(chart_data: ChartData):',
        'chart_data.data should contain the following columns: x, error_max, error_min, legend',
        'The columns received:',
        "Index(['not_x', 'not_error_max', 'not_error_min', 'not_legend'], dtype='object')",
    )
    chart = chart_service.generate_error_bar_chart(chart_data)
    assert caplog.records[0].message == error
    assert caplog.records[0].levelname == 'ERROR'
    assert not chart

    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'x': 10, 'error_max': 100, 'error_min': 10, 'not_legend': 'test legend'},
            {'x': 20, 'error_max': 200, 'error_min': 20, 'not_legend': 'test legend'},
            {'x': 30, 'error_max': 300, 'error_min': 30, 'not_legend': 'test legend'},
        ),
    )

    error = '{0}\n{1}\n{2} {3}\n\n'.format(
        'An error occurred in ChartService::generate_error_bar_chart(chart_data: ChartData):',
        'chart_data.data should contain the following columns: x, error_max, error_min, legend',
        'The columns received:',
        "Index(['x', 'error_max', 'error_min', 'not_legend'], dtype='object')",
    )
    chart = chart_service.generate_error_bar_chart(chart_data)
    assert caplog.records[1].message == error
    assert caplog.records[1].levelname == 'ERROR'

    assert not chart


def test_generate_error_bar_chart_success() -> None:
    """Ensure generate_error_bar_chart successfully produces line charts."""
    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'x': 10, 'error_max': 100, 'error_min': 10, 'legend': 'test legend'},
            {'x': 20, 'error_max': 200, 'error_min': 20, 'legend': 'test legend'},
            {'x': 30, 'error_max': 300, 'error_min': 30, 'legend': 'test legend'},
        ),
    )

    chart = chart_service.generate_error_bar_chart(chart_data)
    assert chart
    assert 'test legend' in chart
    assert 'Test title' in chart
    assert 'Test label x' in chart
    assert 'Test label y' in chart
    assert 'Test label legend' in chart


def test_generate_error_bar_chart_custom_candle_labels() -> None:
    """Ensure generate_error_bar_chart correctly changes candle legend labels."""
    chart_data = CHART_DATA._replace(
        data=pd.DataFrame(
            {'x': 10, 'error_max': 100, 'error_min': 10, 'legend': 'test legend'},
            {'x': 20, 'error_max': 200, 'error_min': 20, 'legend': 'test legend'},
            {'x': 30, 'error_max': 300, 'error_min': 30, 'legend': 'test legend'},
        ),
    )

    chart = chart_service.generate_error_bar_chart(
        chart_data,
        label_error_max='custom error max label',
        label_error_min='custom error min label',
    )
    assert chart
    assert 'custom error max label' in chart
    assert 'custom error min label' in chart
