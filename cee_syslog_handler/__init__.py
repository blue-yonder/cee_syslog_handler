from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

from logging.handlers import SysLogHandler
from logging.handlers import SYSLOG_UDP_PORT
import json
import socket
import traceback
import logging

SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_full_message(exc_info, message):
    return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else message


#see http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def make_message_dict(record, debugging_fields, extra_fields, fqdn, localname, facility=None):
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


#See http://github.com/hoffmann/graypy/blob/master/graypy/handler.py
def get_fields(message_dict, record):
    # skip_list is used to filter additional fields in a log message.
    # It contains all attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    # plus exc_text, which is only found in the logging module source,
    # and id, which is prohibited by the GELF format.
    skip_fields = (
        'args', 'asctime', 'created', 'exc_info',  'exc_text', 'filename',
        'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
        'msecs', 'message', 'msg', 'name', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName')

    for key, value in record.__dict__.items():
        if key not in skip_fields and not key.startswith('_'):
            if isinstance(value, basestring):
                message_dict['_%s' % key] = value
            else:
                message_dict['_%s' % key] = repr(value)
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

    def __init__(self, address=('localhost', SYSLOG_UDP_PORT), socktype=None,
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
                                    self._facility)
        return ": @cee: %s" % json.dumps(message)
