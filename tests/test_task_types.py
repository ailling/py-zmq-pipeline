from zmqpipeline import TaskType
import pytest

def test_task_registration():
    my_task_type = 'MYTASK'
    TaskType.register_type(my_task_type)

    # should not raise an error
    TaskType('MYTASK')


def test_unknown_task_type_error():
    with pytest.raises(TypeError):
        TaskType('UNKNOWN_TASK')


