from zmqpipeline.task import Task
from zmqpipeline import TaskType
from zmqpipeline.utils import messages
from factories.task import TaskFactory, TASK_TYPE_MY_TASK, ENDPOINT_ADDRESS


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



def test_my_task():
    my_task = TaskFactory.build()
    assert my_task.task_type == TaskType(TASK_TYPE_MY_TASK)
    assert my_task.endpoint == ENDPOINT_ADDRESS
    assert my_task.dependencies == []


def test_task_handle():
    task = TaskFactory.build()
    data = {
        'key': 'value'
    }
    assert task.handle(data, '', messages.MESSAGE_TYPE_DATA)

