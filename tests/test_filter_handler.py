import logging
from logging import makeLogRecord

from cee_syslog_handler import NamedCeeLogger, RegexFilter, RegexRedactFilter

_DUMMY_HOST = ("localhost", 1337)
_DUMMY_PROTOCOL = 2


class CollectingNamedCeeLogger(NamedCeeLogger):
    def __init__(self, *args, **kwargs):
        super(CollectingNamedCeeLogger, self).__init__(*args, **kwargs)
        self.emitted_records = []

    def emit(self, record):
        self.emitted_records.append(record)
        return super(CollectingNamedCeeLogger, self).emit(record)


def test_filter():
    filter_regex = r"/health|/metrics"

    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(RegexFilter(filter_regex))

    handler.handle(makeLogRecord({"msg": "POST /important/endpoint 200 OK"}))
    assert len(handler.emitted_records) == 1  # record emitted

    handler.handle(makeLogRecord({"msg": "GET /health 200 OK"}))
    assert len(handler.emitted_records) == 1  # no new record emitted

    handler.handle(makeLogRecord({"msg": "GET /metrics 404"}))
    assert len(handler.emitted_records) == 1  # no new record emitted

    handler.handle(
        makeLogRecord(
            {"msg": "Eating vegetables is healthy and improves blood metrics"}
        )
    )
    assert len(handler.emitted_records) == 2  # new record emitted


def test_redacting_filter():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"

    record = makeLogRecord(
        {"name": "my.package.logger", "msg": "Connect by IP 172.24.41.42"}
    )
    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    handler.handle(record)

    assert len(handler.emitted_records) == 1
    message = handler.emitted_records[0].getMessage()
    assert string_to_be_redacted not in message
    assert replace_string in message


def test_redact_injected_variables():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"

    arbitrary_object = SomeClass("some 172.24.41.42 arbitrary object")
    record = makeLogRecord(
        {
            "name": "my.package.logger",
            "msg": "Connect %d by IP %s %s",
            "args": (42, "172.24.41.42", arbitrary_object),
        }
    )
    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    handler.handle(record)

    assert len(handler.emitted_records) == 1
    message = handler.emitted_records[0].getMessage()
    assert string_to_be_redacted not in message
    assert replace_string in message


def test_redact_exception():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"
    logger = logging.getLogger(__name__)

    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    logger.addHandler(handler)

    arbitrary_object = SomeClass("some 172.24.41.42 arbitrary object")

    try:
        raise MemoryError("something bad: ", string_to_be_redacted, arbitrary_object)
    except MemoryError as e:
        logger.exception(e)

    assert len(handler.emitted_records) == 1
    message = handler.emitted_records[0].getMessage()
    assert string_to_be_redacted not in message
    assert replace_string in message


def test_redact_objects():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"

    logger = logging.getLogger(__name__)
    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    logger.addHandler(handler)

    arbitrary = SomeClass("some message containing" + string_to_be_redacted)
    logger.error(arbitrary)

    assert len(handler.emitted_records) == 1
    message = handler.emitted_records[0].getMessage()
    assert string_to_be_redacted not in message
    assert replace_string in message


def test_exception_not_in_message():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"
    logger = logging.getLogger(__name__)

    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    logger.addHandler(handler)

    try:
        raise MemoryError("something bad: ", string_to_be_redacted)
    except MemoryError:
        logger.exception("Failed to do something")

    assert len(handler.emitted_records) == 1
    message = handler.emitted_records[0].getMessage()
    assert string_to_be_redacted not in message
    assert replace_string in message


def test_exc_text_redaction():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    replace_string = "-#sensitive#-"
    string_to_be_redacted = "172.24.41.42"

    record = makeLogRecord(
        {
            "name": "my.package.logger",
            "msg": "Connect by IP 172.24.41.42",
            "exc_text": "something 192.168.0.1 something",
        }
    )
    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(
        RegexRedactFilter(filter_regex=regex, replace_string=replace_string)
    )
    handler.handle(record)

    assert len(handler.emitted_records) == 1
    exc_text = handler.emitted_records[0].exc_text
    assert string_to_be_redacted not in exc_text
    assert replace_string in exc_text


def test_filter_bypass():
    regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    record = makeLogRecord(
        {
            "name": "my.package.logger",
            "msg": "Attempted connect to %s failed %d times",
            "args": ("web.service", 42),
        }
    )
    handler = CollectingNamedCeeLogger(_DUMMY_HOST, _DUMMY_PROTOCOL, "myname")
    handler.addFilter(RegexRedactFilter(filter_regex=regex))
    handler.handle(record)

    assert len(handler.emitted_records) == 1
    log_record = handler.emitted_records[0]
    assert "Attempted connect to web.service failed 42 times" == log_record.getMessage()
    assert ("web.service", 42) == log_record.args


class SomeClass:
    """
    generic helper class
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message
