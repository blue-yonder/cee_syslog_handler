# coding=utf-8

import logging
import unittest

from cee_syslog_handler import NamedCeeLogger


_DUMMY_HOST = ('localhost', 1337)
_DUMMY_PROTOCOL = 2


def _make_log_record():
    return logging.LogRecord('dummy_logger', logging.DEBUG, 'test.py', 13, 'Dummy message', (), None)


class NamedCeeLoggerTests(unittest.TestCase):
    def _test_format_adds_service_name(self, expected_service_name):
        expected_json_field = '"_name": "{}"'.format(expected_service_name)
        logger = NamedCeeLogger(_DUMMY_HOST, 2, expected_service_name)
        record = _make_log_record()
        self.assertIn(expected_json_field, logger.format(record))

    def test_format_adds_service_name(self):
        """
        Ensure the Cee entry created by format contains the name provided to the logger constructor
        """
        self._test_format_adds_service_name('My Fancy Service')
        self._test_format_adds_service_name('Another Service')


