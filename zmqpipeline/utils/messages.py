
import serializer

MESSAGE_TYPE_ACK = 'ACK'
MESSAGE_TYPE_SUCCESS = 'OK'
MESSAGE_TYPE_FAILURE = 'FAIL'
MESSAGE_TYPE_READY = 'RDY'
MESSAGE_TYPE_END = 'END'
MESSAGE_TYPE_DATA = 'DATA'
MESSAGE_TYPE_META_DATA = 'METADATA'
MESSAGE_TYPE_EMPTY = ''


ALL_MESSAGE_TYPES = [
    MESSAGE_TYPE_ACK,
    MESSAGE_TYPE_SUCCESS,
    MESSAGE_TYPE_FAILURE,
    MESSAGE_TYPE_READY,
    MESSAGE_TYPE_END,
    MESSAGE_TYPE_DATA,
    MESSAGE_TYPE_META_DATA,
    MESSAGE_TYPE_EMPTY
]


def create(data, tasktype, msgtype):
    """
    Creates a message packed as a dictionary keyed on data and msgtype
    :param data:
    :param msgtype:
    :return:
    """
    return serializer.serialize({
        'data': data,
        'task': tasktype,
        'type': msgtype
    })

# data types

def create_data(task, data):
    return create(data, task, MESSAGE_TYPE_DATA)

def create_metadata(metadata):
    return create(metadata, '', MESSAGE_TYPE_META_DATA)


# signal types

def _create_type(ty, task='', data=''):
    return serializer.serialize({
        'data': data,
        'task': task,
        'type': ty
    })


# SPECIAL MESSAGE TYPES - ALL OF THESE HAVE EMPTY DATA

def create_ack(task = '', data=''):
    return _create_type(MESSAGE_TYPE_ACK, task, data)

def create_success(task = '', data=''):
    return _create_type(MESSAGE_TYPE_SUCCESS, task, data)

def create_failure(task = '', data=''):
    return _create_type(MESSAGE_TYPE_FAILURE, task, data)

def create_empty(task = '', data=''):
    return _create_type(MESSAGE_TYPE_EMPTY, task, data)

def create_ready(task = '', data=''):
    return _create_type(MESSAGE_TYPE_READY, task, data)

def create_end(task = '', data=''):
    return _create_type(MESSAGE_TYPE_END, task, data)



def get(msg):
    """
    Returns the tuple: data, message-type
    :param msg:
    :return:
    """
    d = serializer.deserialize(msg)
    return (
        d.get('data', {}),
        d.get('task', ''),
        d.get('type', MESSAGE_TYPE_EMPTY),
    )

