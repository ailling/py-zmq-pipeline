from datetime import datetime, timedelta, date

import pytest
import zmqpipeline
from zmqpipeline.utils import serializer
import pdb


def test_basic():
    data = {
        'somestr': 'something',
        'someint': 5,
        'somelist': range(1,5)
    }

    assert serializer.deserialize(serializer.serialize(data)) == data

def test_datetime():
    data = {
        'dt': datetime.now()
    }
    sdata = serializer.serialize(data)
    assert type(sdata) is str

    dsdata = serializer.deserialize(sdata)
    assert isinstance(dsdata['dt'], datetime)

def test_timedelta():
    data = {
        'td': timedelta(minutes=45)
    }
    sdata = serializer.serialize(data)
    assert type(sdata) is str

    dsdata = serializer.deserialize(sdata)
    assert isinstance(dsdata['td'], timedelta)

def test_date():
    data = {
        'date': datetime.today().date()
    }
    sdata = serializer.serialize(data)
    assert type(sdata) is str

    dsdata = serializer.deserialize(sdata)
    assert isinstance(dsdata['date'], date)

