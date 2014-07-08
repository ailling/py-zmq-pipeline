import zmqpipeline
import settings
import time


class CalculationTask(zmqpipeline.Task):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_CALC)
    endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
    dependencies = []
    n_count = 0

    def handle(self, data, address, msgtype):
        """
        Simulates some work to be done
        :param data:
        :param address:
        :param msgtype:
        :return:
        """
        self.n_count += 1
        if self.n_count >= 100:
            # mark as complete after 1000 executions. Should take a total of 10 seconds to run sequentially
            self.is_complete = True

        # return the work to be done on the worker
        return {
            'workload': .01
        }

