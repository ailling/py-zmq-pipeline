import common
from zmqpipeline import Distributor, EndpointAddress

COLLECTOR_ENDPOINT = 'tcp://localhost:5551'
COLLECTOR_ACK_ENDPOINT = 'tcp://localhost:5552'

class DistributorFactory(common.FlexibleObjectFactory):
    class Meta:
        model = Distributor

    collector_endpoint = EndpointAddress(COLLECTOR_ENDPOINT)
    collector_ack_endpoint = EndpointAddress(COLLECTOR_ACK_ENDPOINT)

    receive_metadata = False
    metadata_endpoint = None

