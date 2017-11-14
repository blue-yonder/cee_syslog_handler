Changelog
=========

0.5.0 (2017-11-14)
------------------

*   CeeSysLogHandler now supports custom static keyword arguments that will be
    statically injected into each message. NamedCeeLogger is hereby deprecated.
*   Add RegexFilter to suppress logging of messages containing the match of a
    a given regular expression.
*   The `host` field will now always contain the fully qualified domain name.
*   Remove hardcoded `version` field.
*   Remove support for Python 2.6.

0.4.1 (2017-05-27)
------------------
*   Add NamedCeeLogger

0.3.4 (2016-12-23)
------------------
*   Add JsonFormatter

0.3.3
-----

*   Custom log record fields with leading underscore are now contained in
    the log message. In case the (otherwise) same custom field exists both
    with and without leading underscore, the one with leading underscore has
    precedence.

0.3.2 (2015-03-18)
------------------

* Fix injection of custom facility

0.3.1 (2015-03-09)
------------------

* Fix trove classifier syntax

0.3.0 (2015-03-09)
------------------

* Add support for numeric types
* Add tests
