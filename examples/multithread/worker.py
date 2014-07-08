import settings
import zmqpipeline
from zmqpipeline.utils import shutdown
import time

class MyWorker(zmqpipeline.MultiThreadedWorker):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_CALC)
    endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
    collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

    n_threads = 10
    n_executions = 0

    def handle_execution(self, data, *args, **kwargs):
        """
        Handles execution of the main worker
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        # forward all received data to the thread
        self.n_executions += 1
        return data


    def handle_thread_execution(self, data, index):
        workload = data['workload']
        time.sleep(workload)

        # returning nothing forwards no extra information to the collector

if __name__ == '__main__':
    worker = MyWorker()
    print 'worker running'
    worker.run()

    print 'finished - handled %d executions' % worker.n_executions
    shutdown.kill_current_process()

