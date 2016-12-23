import json

from logging import makeLogRecord

from cee_syslog_handler import CeeSysLogHandler, JsonFormatter

def test_default_facility():
    record = makeLogRecord( {'name':'my.package.logger'} )
    handler = CeeSysLogHandler()

    assert '"facility": "my.package.logger"' in handler.format(record)


def test_custom_facility():
    record = makeLogRecord( {'name':'my.package.logger'} )
    handler = CeeSysLogHandler(facility='my.custom.facility')

    assert '"facility": "my.custom.facility"' in handler.format(record)
    assert '"_logger": "my.package.logger"' in handler.format(record)


def test_custom_field():
    record = makeLogRecord( {'name':'my.package.logger'} )
    record.custom_field = "custom value"
    handler = CeeSysLogHandler()

    assert '"_custom_field": "custom value"' in handler.format(record)


def test_custom_field_with_leading_underscore():
    record = makeLogRecord( {'name':'my.package.logger'} )
    record._custom_field = "custom value"
    handler = CeeSysLogHandler()

    assert '"_custom_field": "custom value"' in handler.format(record)


def test_custom_fields_with_underscores_have_precendence():
    record = makeLogRecord( {'name':'my.package.logger'} )
    record.foo = "should not appear in output"
    record._foo = "has precedence"
    handler = CeeSysLogHandler()

    assert 'has precedence' in handler.format(record)
    assert 'should not appear in output' not in handler.format(record)


def test_id_field_not_supported():
    record = makeLogRecord( {'name':'my.package.logger'} )
    record.id = "custom value"
    record._id = "some other value value"
    handler = CeeSysLogHandler()

    assert '"_id"' not in handler.format(record)


class _BadStringRepresentation(object):
    def __str__(self):
        raise RuntimeError("I misbehave")


def test_custom_field_with_raising_str():
    record = makeLogRecord( {'name':'my.package.logger'} )
    record._custom_field = _BadStringRepresentation()
    handler = CeeSysLogHandler()

    assert '"_custom_field": "value could not be converted to str"' in handler.format(record)

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







