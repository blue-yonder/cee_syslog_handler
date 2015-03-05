from cee_syslog_handler import get_fields

class Record(object):
    pass

def test_get_fields_empty():
    record =  Record()
    message_dict = get_fields({}, record)
    assert message_dict == {}
