import settings
import zmqpipeline
from zmqpipeline.utils import shutdown
import time


class SecondWorker(zmqpipeline.SingleThreadedWorker):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_SECOND)
    endpoint = zmqpipeline.EndpointAddress(settings.SECOND_WORKER_ENDPOINT)
    collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

    n_executions = 0

    def handle_execution(self, data, *args, **kwargs):
        self.n_executions += 1

        workload = data['workload']
        print 'second worker - working for %f seconds' % workload
        time.sleep(workload)

        # returning nothing forwards no extra information to the collector

if __name__ == '__main__':
    worker = SecondWorker()
    print 'worker running'
    worker.run()

    print 'finished - handled %d executions' % worker.n_executions
    shutdown.kill_current_process()

