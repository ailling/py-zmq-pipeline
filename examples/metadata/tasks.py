import settings
import zmqpipeline

class MyTask(zmqpipeline.Task):
    task_type = zmqpipeline.TaskType(settings.TASK_TYPE_MY_TASK)
    endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
    dependencies = []

    def handle(self, data, address, msgtype):
        """
        Sends one message and prints the contents of the meta variable.
        Meta data is forwarded to the worker.
        :param data: Data received from distributor
        :param address: The address of the client where task output will be sent
        :param msgtype: the type of message received. Typically zmqpipeline.utils.messages.MESSAGE_TYPE_DATA
        :return:
        """
        self.is_complete = True

        meta_variable = data['meta_variable']
        print 'MyTask: meta_variable is: ', meta_variable

        # forward data to the worker
        return data

