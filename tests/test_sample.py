import pytest

import zmqpipeline
from zmqpipeline.helpers import valid_endpoint
import pdb

def func(x):
    return x + 1

def test_answer():
    assert func(3) == 4

def test_valid_address():
    addr = zmqpipeline.EndpointAddress('tcp://localhost:5558')
    assert valid_endpoint(addr) == True

def test_invalid_address1():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('blah')


def test_invalid_address1():
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('tpc://badprotocol')


def test_invalid_address1():
    """
    something
    :return:
    """
    "something"
    with pytest.raises(AttributeError):
        addr = zmqpipeline.EndpointAddress('tcp:/badformat')

