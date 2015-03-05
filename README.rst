==================
cee_syslog_handler
==================

.. image:: https://travis-ci.org/blue-yonder/cee_syslog_handler.svg?branch=master 
    :target: https://travis-ci.org/blue-yonder/cee_syslog_handler


Python Syslog Logging Handler with CEE Support

Usage::

    from cee_syslog_handler import CeeSysLogHandler
    import logging

    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)

    ch = CeeSysLogHandler(address=("10.2.160.20", 514))
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    logger.info("test")



