from zmqpipeline.utils import messages

TEST_TASK = 'TSTSK'

def test_create_data_msg():
    inputdata = {
        'key1': 'value1',
        'key2': 10
    }
    msg = messages.create_data(TEST_TASK, inputdata)
    data, tt, msgtype = messages.get(msg)
    assert tt == TEST_TASK
    assert msgtype == messages.MESSAGE_TYPE_DATA
    assert data == inputdata


def test_create_metadata_msg():
    metadata = {
        'key1': 'value',
        'key2': 100
    }
    msg = messages.create_metadata(metadata)
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_META_DATA
    assert data == metadata


def test_create_ack_msg():
    msg = messages.create_ack()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_ACK


def test_create_success_msg():
    msg = messages.create_success()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_SUCCESS

def test_create_failure_msg():
    msg = messages.create_failure()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_FAILURE

def test_create_empty_msg():
    msg = messages.create_empty()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_EMPTY

def test_create_ready_msg():
    msg = messages.create_ready()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_READY

def test_create_end_msg():
    msg = messages.create_end()
    data, tt, msgtype = messages.get(msg)
    assert tt == ''
    assert msgtype == messages.MESSAGE_TYPE_END

