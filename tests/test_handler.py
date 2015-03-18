from cee_syslog_handler import CeeSysLogHandler
from logging import makeLogRecord


def test_default_facility():
    record = makeLogRecord( {'name':'my.package.logger'} )
    handler = CeeSysLogHandler()

    assert '"facility": "my.package.logger"' in handler.format(record)


def test_custom_facility():
    record = makeLogRecord( {'name':'my.package.logger'} )
    handler = CeeSysLogHandler(facility='my.custom.facility')

    assert '"facility": "my.custom.facility"' in handler.format(record)
    assert '"_logger": "my.package.logger"' in handler.format(record)

