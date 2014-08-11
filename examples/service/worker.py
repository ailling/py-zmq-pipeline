import settings
from zmqpipeline import TaskType, EndpointAddress, ServiceWorker
import time


class MyWorker(ServiceWorker):

    task_type = TaskType(settings.TASK_TYPE_MY_TASK)
    endpoint = EndpointAddress(settings.BACKEND_ENDPOINT)

    def handle_message(self, data, task_type, msgtype):
        """
        Turns messages into upper-cased format

        :param data:
        :param task_type:
        :param msgtype:
        :return:
        """
        data['message'] = data['message'].upper()
        time.sleep(.01)
        return data



if __name__ == '__main__':
    worker = MyWorker()

    print 'running MyWorker instance'
    worker.run()

    print 'finished'

