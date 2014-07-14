from zmqpipeline.task import Task
from zmqpipeline import EndpointAddress, TaskType
from factories.task import TaskFactory

TASK_TYPE_MY_TASK = 'MYTASK'
TaskType.register_type(TASK_TYPE_MY_TASK)

def test_initialization():
    task = TaskFactory.build()
    metadata = {
        'key1': 'value1',
        'key2': 100
    }
    task.initialize(metadata)
    assert task.metadata == metadata


def test_registration():
    task = TaskFactory.build()
    Task.register_task_instance(task)
    ls = []
    for items in Task.task_instances.values():
        for item in items:
            ls.append(item)
    assert task in ls


class MyTask(Task):
    task_type = TaskType(TASK_TYPE_MY_TASK)
    endpoint = EndpointAddress('ipc://worker.ipc')
    dependencies = []

def test_my_task():
    my_task = MyTask()
    assert my_task.task_type == TaskType(TASK_TYPE_MY_TASK)
    assert my_task.endpoint == EndpointAddress('ipc://worker.ipc')
    assert my_task.dependencies == []


