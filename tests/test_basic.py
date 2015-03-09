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
    check_single_value('1')
    check_single_value('1.1')

def test_numeric_types():
    check_single_value(1.1)
    check_single_value(1)
