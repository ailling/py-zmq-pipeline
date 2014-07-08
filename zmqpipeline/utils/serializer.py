from datetime import datetime, date, timedelta
import msgpack

def unix_time(dt):
    if isinstance(dt, timedelta):
        return dt.total_seconds()
    elif isinstance(dt, datetime):
        epoch = datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return delta.total_seconds()
    elif isinstance(dt, date):
        epoch = datetime.utcfromtimestamp(0).date()
        delta = dt - epoch
        return delta.total_seconds()
    else:
        raise Exception('unix_time: unacceptable type passed as argument')


def decode_datetime(obj):
    if b'__datetime__' in obj:
        obj = datetime.utcfromtimestamp(obj['epochs'])
    elif b'__date__' in obj:
        obj = datetime.utcfromtimestamp(obj['epochs']).date()
    elif b'__timedelta__' in obj:
        obj = timedelta(seconds = obj['epochs'])
    return obj


def encode_datetime(obj):
    if isinstance(obj, datetime):
        return {
            b'__datetime__': True,
            b'epochs': unix_time(obj)
        }

    if isinstance(obj, date):
        return {
            b'__date__': True,
            b'epochs': unix_time(obj)
        }

    if isinstance(obj, timedelta):
        return {
            b'__timedelta__': True,
            b'epochs': unix_time(obj)
        }

    return obj

def serialize(data):
    return msgpack.packb(data, default = encode_datetime)

def deserialize(msg):
    return msgpack.unpackb(msg, object_hook = decode_datetime)
