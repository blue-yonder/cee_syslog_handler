from logging import makeLogRecord

from cee_syslog_handler import NamedCeeLogger, RegexFilter


_DUMMY_HOST = ('localhost', 1337)
_DUMMY_PROTOCOL = 2


class CollectingNamedCeeLogger(NamedCeeLogger):
    def __init__(self, *args, **kwargs):
        super(CollectingNamedCeeLogger, self).__init__(*args, **kwargs)
        self.emitted_records = []

    def emit(self, record):
        self.emitted_records.append(record)
        return super(CollectingNamedCeeLogger, self).emit(record)


def test_filter():
    filter_regex = r'/health|/metrics'

    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, 'myname')
    handler.addFilter(RegexFilter(filter_regex))

    handler.handle(makeLogRecord({'msg': 'POST /important/endpoint 200 OK'}))
    assert len(handler.emitted_records) == 1 # record emitted

    handler.handle(makeLogRecord({'msg': 'GET /health 200 OK'}))
    assert len(handler.emitted_records) == 1 # no new record emitted

    handler.handle(makeLogRecord({'msg': 'GET /metrics 404'}))
    assert len(handler.emitted_records) == 1 # no new record emitted

    handler.handle(makeLogRecord({'msg': 'Eating vegetables is healthy and improves blood metrics'}))
    assert len(handler.emitted_records) == 2 # new record emitted
