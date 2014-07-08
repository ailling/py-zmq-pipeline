import settings
import zmqpipeline
from zmqpipeline.utils import shutdown
import time

class FirstWorker(zmqpipeline.SingleThreadedWorker):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_FIRST)
    endpoint = zmqpipeline.EndpointAddress(settings.FIRST_WORKER_ENDPOINT)
    collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

    n_executions = 0

    def handle_execution(self, data, *args, **kwargs):
        self.n_executions += 1

        workload = data['workload']
        print 'first worker - working for %f seconds' % workload
        time.sleep(workload)

        # returning nothing forwards no extra information to the collector

if __name__ == '__main__':
    worker = FirstWorker()
    print 'worker running'
    worker.run()

    print 'finished - handled %d executions' % worker.n_executions
    shutdown.kill_current_process()

