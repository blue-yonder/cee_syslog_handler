from cee_syslog_handler import get_fields


class Record(object):
    def __init__(self, value=None):
        if value:
            self.some_column = value 


def check_single_value(value):
    record = Record(value)
    message_dict = get_fields({}, record)
    assert message_dict == {'_some_column': value}

def test_get_fields_empty():
    record =  Record()
    message_dict = get_fields({}, record)
    assert message_dict == {}

def test_string_types():
    check_single_value('some_text')
    check_single_value(u'some_text')

def test_numeric_types():
    pi = 3.1415

    class SomeType(object):
        def __init__(self):
            self._value = pi

        def __float__(self):
            return self._value

        def __eq__(self, value):
            return float(value) == self._value

    check_single_value(1.1)
    check_single_value(1)
    assert float(SomeType()) == pi
    check_single_value(SomeType())
