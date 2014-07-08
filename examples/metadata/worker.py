import settings
import zmqpipeline
from zmqpipeline.utils import shutdown

class MyWorker(zmqpipeline.SingleThreadedWorker):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_MY_TASK)
    endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
    collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

    def handle_execution(self, data, *args, **kwargs):
        meta_variable = data['meta_variable']
        print 'MyWorker: meta variable is %s' % meta_variable


if __name__ == '__main__':
    worker = MyWorker()
    print 'worker running'
    worker.run()

    print 'worker finished'
    shutdown.kill_current_process()

