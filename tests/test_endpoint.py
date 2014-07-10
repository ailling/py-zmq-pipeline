import pytest
import zmqpipeline
from zmqpipeline.helpers import valid_endpoint, endpoint_binding


def test_valid_address():
    addr = zmqpipeline.EndpointAddress('tcp://localhost:5558')
    assert valid_endpoint(addr) == True

def test_invalid_address_1():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('blah')


def test_invalid_address_2():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('tpc://badprotocol:1000')


def test_invalid_address_3():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('tcp:/badformat:1000')

def test_invalid_address_4():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('tcp://incomplete')


def test_invalid_address_5():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('')

def test_binding_1():
    assert endpoint_binding('tcp://localhost:1000') == 'tcp://*:1000'

def test_binding_2():
    assert endpoint_binding('inproc://test') == 'inproc://test'

def test_binding_3():
    assert endpoint_binding('ipc://test.ipc') == 'ipc://test.ipc'


