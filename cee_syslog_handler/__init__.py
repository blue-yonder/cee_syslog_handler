from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

from logging.handlers import SysLogHandler
from logging.handlers import SYSLOG_UDP_PORT
import json
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
_STANDARD_FIELDS = ('args', 'asctime', 'created', 'exc_info', 'exc_text',
                  'filename', 'funcName', 'levelname', 'levelno',
                  'lineno', 'module', 'msecs', 'message', 'msg', 'name',
                  'pathname', 'process', 'processName', 'relativeCreated',
                  'stack_info', 'thread', 'threadName')

# The GELF format does not support "_id" fields
_SKIPPED_FIELDS = _STANDARD_FIELDS + ('id', '_id')


_SUPPORTED_OUTPUT_TYPES = (string_type, float) + integer_type


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_full_message(exc_info, message):
    return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else message


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def make_message_dict(record, debugging_fields, extra_fields, fqdn, localname, facility):
    if fqdn:
        host = socket.getfqdn()
    elif localname:
        host = localname
    else:
        host = socket.gethostname()
    message_dict = {
        'version': "1.0",
        'host': host,
        'short_message': record.getMessage(),
        'message': get_full_message(record.exc_info, record.getMessage()),
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
        })
        # record.processName was added in Python 2.6.2
        pn = getattr(record, 'processName', None)
        if pn is not None:
            message_dict['_process_name'] = pn
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


#See http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_fields(message_dict, record):
    fields = record.__dict__
    for key in sorted(fields.keys(), reverse=True):
        value = fields[key]
        if key not in _SKIPPED_FIELDS:
            message_dict[_custom_key(key)] = _to_supported_output_type(value)

    return message_dict


class CeeSysLogHandler(SysLogHandler):
    """
    A syslog handler that formats extra fields as a CEE compatible structured log message. A CEE compatible message is
    a syslog log entry that contains a cookie string "@cee:" in its message part. Everything behind the colon is
    expected to be a JSON dictionary (containing no lists as children).

    See the following links for the specification of the CEE syntax:
    http://www.rsyslog.com/doc/mmpstrucdata.html
    http://cee.mitre.org
    http://cee.mitre.org/language/1.0-beta1/clt.html#appendix-1-cee-over-syslog-transport-mapping

    The handler is compatible to graypy and emits the same structured log messages as the graypy gelf handler does.

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

    def __init__(self, address=('localhost', SYSLOG_UDP_PORT), socktype=socket.SOCK_DGRAM,
                 debugging_fields=True, extra_fields=True, facility=None):
        """

        :param address: Address of the syslog server (hostname, port)
        :param socktype: If specified (socket.SOCK_DGRAM or socket.SOCK_STREAM) uses UDP or TCP respectively
        :param debugging_fields: Whether to include file, line number, function, process and thread id in the log
        :param extra_fields: Whether to include extra fields (submitted via the keyword argument extra to a logger)
                             in the log dictionary
        :param facility: If not specified uses the logger's name as facility
        """
        super(CeeSysLogHandler, self).__init__(address, facility=SysLogHandler.LOG_USER, socktype=socktype)
        self._debugging_fields = debugging_fields
        self._extra_fields = extra_fields
        self._facility = facility

    def format(self, record):
        message = make_message_dict(record,
                                    self._debugging_fields,
                                    self._extra_fields,
                                    False,
                                    None,
                                    self._facility)
        return ": @cee: %s" % json.dumps(message)
