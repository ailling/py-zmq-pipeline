import common
from zmqpipeline import Distributor

class DistributorFactory(common.FlexibleObjectFactory):
    class Meta:
        model = Distributor


