import pytest

from app.observability.request_trace import RequestTrace


def test_add_metric_is_recorded():
    trace = RequestTrace(operation="test")

    trace.add_metric("chunks_used", 3)

    assert trace._metrics == {"chunks_used": 3}


def test_add_metric_rejects_empty_name():
    trace = RequestTrace(operation="test")

    with pytest.raises(ValueError):
        trace.add_metric("  ", 1)
