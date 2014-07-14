import common
from zmqpipeline import Collector

class CollectorFactory(common.FlexibleObjectFactory):
    class Meta:
        model = Collector


