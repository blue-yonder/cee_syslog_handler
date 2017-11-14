from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT
from datetime import datetime
import json
import re
import socket
import sys
import traceback
import logging


PY3 = sys.version_info[0] == 3

if PY3:
    string_type = str
    integer_type = int,
else:
    string_type = basestring
    integer_type = (int, long)

SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


# The following fields are standard log record fields according to
# http://docs.python.org/library/logging.html#logrecord-attributes
# Hint: exc_text is a cache field used by the logging module
_STANDARD_FIELDS = set(('args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message', 'msg', 'name',
    'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'))


# The GELF format does not support "_id" fields
_SKIPPED_FIELDS = _STANDARD_FIELDS | set(('id', '_id'))


_SUPPORTED_OUTPUT_TYPES = (string_type, float) + integer_type


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_full_message(exc_info, message):
    return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else message


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def make_message_dict(record, fqdn, debugging_fields, extra_fields, facility, static_fields):
    message = record.getMessage()
    message_dict = {
        'host': fqdn,
        'short_message': message,
        'message': get_full_message(record.exc_info, message),
        'timestamp': record.created,
        'level': SYSLOG_LEVELS.get(record.levelno, record.levelno),
        'facility': facility or record.name,
        'source_facility': facility or record.name,
    }

    if facility is not None:
        message_dict.update({
            '_logger': record.name
        })

    if debugging_fields:
        message_dict.update({
            'file': record.pathname,
            'line': record.lineno,
            '_function': record.funcName,
            '_pid': record.process,
            '_thread_name': record.threadName,
            '_process_name': record.processName
        })

    message_dict.update(static_fields)

    if extra_fields:
        message_dict = get_fields(message_dict, record)

    return message_dict


def _to_supported_output_type(value):
    if not isinstance(value, _SUPPORTED_OUTPUT_TYPES):
        try:
            return str(value)
        except:
            #make logging nothrow
            return 'value could not be converted to str'
    else:
        return value


def _custom_key(key):
    if key.startswith('_'):
        return key
    else:
        return '_{}'.format(key)


def _sanitize_fields(fields):
    return {_custom_key(k): _to_supported_output_type(v) for k, v in fields.items()}


#See http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_fields(message_dict, record):
    fields = record.__dict__
    unskipped_field_names = set(fields.keys()) - _SKIPPED_FIELDS

    for key in sorted(unskipped_field_names, reverse=True):
        value = fields[key]
        message_dict[_custom_key(key)] = _to_supported_output_type(value)

    return message_dict


class JsonFormatter(logging.Formatter):
    """ A Json Formatter for Python Logging
    Usage:
        import logging
        from cee_syslog_handler import JsonFormatter

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler('spam.log')
        fh.setLevel(logging.DEBUG)

        fh.setFormatter(JsonFormatter())
        logger.addHandler(fh)

        logger.warn("foo")
    """

    def __init__(
            self,
            datefmt='%Y-%m-%dT%H:%M:%S.%f',
            debugging_fields=True,
            extra_fields=True,
            **kwargs):
        """
        :param datefmt: The date formatting
        :param debugging_fields: Whether to include file, line number, function, process and thread
            id in the log
        :param extra_fields: Whether to include extra fields (submitted via the keyword argument
            extra to a logger) in the log dictionary
        :param facility: If not specified uses the logger's name as facility
        :param kwargs: Additional static fields to be injected in each message.
        """
        self.datefmt = datefmt
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self._static_fields = _sanitize_fields(kwargs)
        self._fqdn = socket.getfqdn()

    def format(self, record):
        record = make_message_dict(
            record,
            fqdn=self._fqdn,
            debugging_fields=self.debugging_fields,
            extra_fields=self.extra_fields,
            facility=None,
            static_fields=self._static_fields)

        record["timestamp"] = datetime.fromtimestamp(record["timestamp"]).strftime(self.datefmt)
        del record["short_message"]
        del record["source_facility"]
        return json.dumps(record)


class CeeSysLogHandler(SysLogHandler):
    """
    A syslog handler that formats extra fields as a CEE compatible structured log message. A CEE
    compatible message is a syslog log entry that contains a cookie string "@cee:" in its message
    part. Everything behind the colon is expected to be a JSON dictionary (containing no lists as
    children).

    See the following links for the specification of the CEE syntax:
    http://www.rsyslog.com/doc/mmpstrucdata.html
    http://cee.mitre.org
    http://cee.mitre.org/language/1.0-beta1/clt.html#appendix-1-cee-over-syslog-transport-mapping

    The handler is compatible to graypy and emits the same structured log messages as the graypy
    gelf handler does.

    Usage::

        import logging
        from cee_syslog_handler import CeeSysLogHandler

        logger = logging.getLogger('simple_example')
        logger.setLevel(logging.DEBUG)

        ch = CeeSysLogHandler(address=("10.2.160.20", 514))
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)

        logger.debug('debug message')
        logger.info('info message', extra=dict(foo="bar"))

    Expected Ouput on the syslog side::

        Sep  9 09:31:11 10.128.4.107 : @cee: {"message": "XXXXXXXXXXXX debug message", "level": 7}
        Sep  9 09:31:11 10.128.4.107 : @cee: {"_foo": "bar", "message": "XXXXXXXXXXX info message", "level": 6}

    """

    def __init__(
            self,
            address=('localhost', SYSLOG_UDP_PORT),
            socktype=socket.SOCK_DGRAM,
            debugging_fields=True,
            extra_fields=True,
            facility=None,
            **kwargs):
        """

        :param address: Address of the syslog server (hostname, port)
        :param socktype: If specified (socket.SOCK_DGRAM or socket.SOCK_STREAM) uses UDP or TCP
            respectively
        :param debugging_fields: Whether to include file, line number, function, process and thread
            id in the log
        :param extra_fields: Whether to include extra fields (submitted via the keyword argument
            extra to a logger) in the log dictionary
        :param facility: If not specified uses the logger's name as facility
        :param kwargs: Additional static fields to be injected in each message.
        """
        super(CeeSysLogHandler, self).__init__(
            address,
            facility=SysLogHandler.LOG_USER,
            socktype=socktype)
        self._debugging_fields = debugging_fields
        self._extra_fields = extra_fields
        self._facility = facility
        self._static_fields = _sanitize_fields(kwargs)
        self._fqdn = socket.getfqdn()

    def format(self, record):
        message = make_message_dict(
            record,
            self._fqdn,
            self._debugging_fields,
            self._extra_fields,
            self._facility,
            self._static_fields)
        return ": @cee: %s" % json.dumps(message)


class NamedCeeLogger(CeeSysLogHandler):

    def __init__(self, address, socket_type, name):
        super(NamedCeeLogger, self).__init__(address, socket_type, name=name)


class RegexFilter(logging.Filter):
    """
    This Filter can be used to discard log messages that contain a match of
    a given regular expression.
    """
    def __init__(self, filter_regex):
        super(RegexFilter, self).__init__()
        self._pattern = re.compile(filter_regex)

    def filter(self, record):
        """
        Returns True if the record shall be logged. False otherwise.

        https://github.com/python/cpython/blob/2.7/Lib/logging/__init__.py#L607
        """
        found = self._pattern.search(record.getMessage())
        return not found
