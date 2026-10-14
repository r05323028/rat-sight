import logging

from ratsight_api.infrastructure.logging import JsonFormatter


def test_json_log_formatter_emits_parseable_structured_event() -> None:
    record = logging.LogRecord("ratsight.test", logging.INFO, "test.py", 1, "ready", (), None)
    output = JsonFormatter().format(record)
    assert '"level": "INFO"' in output
    assert '"message": "ready"' in output
