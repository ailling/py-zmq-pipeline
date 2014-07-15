import common
from zmqpipeline import MetaDataWorker, SingleThreadedWorker, MultiThreadedWorker,\
    EndpointAddress, TaskType

META_WORKER_ENDPOINT = 'tcp://localhost:5550'
COLLECTOR_ENDPOINT = 'tcp://localhost:5551'
WORKER_ENDPOINT = 'tcp://localhost:5553'

TASK_TYPE_ST = 'ST'
TASK_TYPE_MT = 'MT'

TaskType.register_type(TASK_TYPE_ST)
TaskType.register_type(TASK_TYPE_MT)


class TestMetaDataWorker(MetaDataWorker):
    endpoint = EndpointAddress(META_WORKER_ENDPOINT)

    def get_metadata(self):
        return {
            'key1': 'some meta',
            'key2': 1000
        }


class MetaDataWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = TestMetaDataWorker




class TestSingleThreadedWorker(SingleThreadedWorker):
    task_type = TaskType(TASK_TYPE_ST)

    endpoint = EndpointAddress(WORKER_ENDPOINT)
    collector_endpoint = EndpointAddress(COLLECTOR_ENDPOINT)

    def handle_execution(self, data, *args, **kwargs):
        return data


class SingleThreadedWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = TestSingleThreadedWorker




class TestMultiThreadWorker(MultiThreadedWorker):
    task_type = TaskType(TASK_TYPE_MT)

    endpoint = EndpointAddress(WORKER_ENDPOINT)
    collector_endpoint = EndpointAddress(COLLECTOR_ENDPOINT)

    n_threads = 1

    def handle_execution(self, data, *args, **kwargs):
        return data

    def handle_thread_execution(self, data, index):
        return data


class MultiThreadedWorkerFactory(common.FlexibleObjectFactory):
    class Meta:
        model = TestMultiThreadWorker


