import common
from zmqpipeline import Collector, EndpointAddress

class TestCollector(Collector):
    endpoint = EndpointAddress('tcp://localhost:5551')
    ack_endpoint = EndpointAddress('tcp://localhost:5552')

    def handle_collection(self, data, task_type, msgtype):
        return data

    def handle_finished(self, data, task_type):
        return data


class CollectorFactory(common.FlexibleObjectFactory):
    class Meta:
        model = TestCollector

