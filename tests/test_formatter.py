import json
from logging import makeLogRecord

from cee_syslog_handler import JsonFormatter


def test_json_formatter():
    fmt = JsonFormatter()
    record = makeLogRecord( {'name':'my.package.logger'} )
    res = fmt.format(record)

    assert '"facility": "my.package.logger' in res

    d = json.loads(res)
    assert isinstance(d, dict)
    for f in ["file", "line", "_function", "_pid", "_thread_name"]:
        assert f in d


def test_json_formatter_options():
    fmt = JsonFormatter(debugging_fields=False)
    record = makeLogRecord( {'name':'my.package.logger', 'special_field': 10} )
    res = fmt.format(record)

    d = json.loads(res)
    assert isinstance(d, dict)
    for f in ["file", "line", "_function", "_pid", "_thread_name"]:
        assert f not in d

    assert d["_special_field"] == 10

    fmt = JsonFormatter(datefmt='%Y-%m-%d',)
    record = makeLogRecord( {'name':'my.package.logger', 'special_field': 10} )
    res = fmt.format(record)

    d = json.loads(res)
    assert len(d["timestamp"]) == 10

    fmt = JsonFormatter(extra_fields=False)
    record = makeLogRecord( {'name':'my.package.logger', 'special_field': 10} )
    res = fmt.format(record)

    d = json.loads(res)
    assert "_special_field" not in d
