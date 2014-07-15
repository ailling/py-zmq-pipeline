import common
from zmqpipeline import Task
from zmqpipeline import EndpointAddress, TaskType

TASK_TYPE_MY_TASK = 'MYTASK'
TaskType.register_type(TASK_TYPE_MY_TASK)
ENDPOINT_ADDRESS = 'ipc://worker.ipc'

class TestTask(Task):
    task_type = TaskType(TASK_TYPE_MY_TASK)
    endpoint = EndpointAddress(ENDPOINT_ADDRESS)
    dependencies = []

    def handle(self, data, address, msgtype):
        return data


class TaskFactory(common.FlexibleObjectFactory):
    class Meta:
        model = TestTask

