# coding=utf-8

import logging

from cee_syslog_handler import NamedCeeLogger


_DUMMY_HOST = ('localhost', 1337)
_DUMMY_PROTOCOL = 2


def _check_format_adds_service_name(expected_service_name):
    expected_json_field = '"_name": "{}"'.format(expected_service_name)
    logger = NamedCeeLogger(_DUMMY_HOST, 2, expected_service_name)
    record = logging.LogRecord('dummy_logger', logging.DEBUG, 'test.py', 13, 'Dummy message', (), None)

    assert expected_json_field in logger.format(record)


def test_format_adds_service_name():
    """
    Ensure the Cee entry created by format contains the name provided to the logger constructor
    """
    _check_format_adds_service_name('My Fancy Service')
    _check_format_adds_service_name('Another Service')
