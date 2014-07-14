import common
from zmqpipeline import MetaDataWorker, SingleThreadedWorker, MultiThreadedWorker


class MetaDataWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = MetaDataWorker


class SingleThreadedWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = SingleThreadedWorker


class MultiThreadedWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = MultiThreadedWorker


