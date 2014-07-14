import common
from zmqpipeline import Task

class TaskFactory(common.FlexibleObjectFactory):
    class Meta:
        model = Task


