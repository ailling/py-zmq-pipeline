from factories.collector import CollectorFactory
from zmqpipeline.utils import messages


def test_instantiation():
    CollectorFactory.build()
    CollectorFactory.create()
    assert True


def test_endpoints():
    cl = CollectorFactory.build()
    cl.endpoint == 'tcp://localhost:5551'
    cl.ack_endpoint == 'tcp://localhost:5552'
    assert True

def test_handle_collection():
    cl = CollectorFactory.build()
    data = {
        'key': 'value'
    }
    assert cl.handle_collection(data, '', messages.MESSAGE_TYPE_DATA) == data

def test_handle_finished():
    cl = CollectorFactory.build()
    data = {
        'key': 'value'
    }
    assert cl.handle_finished(data, '') == data

