from abc import ABCMeta, abstractmethod, abstractproperty

import zmq
from utils import messages
import helpers


class CollectorMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        if name != 'Collector':
            pass

        return super(CollectorMeta, cls).__new__(cls, name, bases, dct)



class Collector(object):
    __metaclass__ = CollectorMeta

    @abstractproperty
    def endpoint(self):
        return ''

    @abstractproperty
    def ack_endpoint(self):
        return ''


    def __init__(self):
        self.context = zmq.Context()

        print 'endpoint: %s' % self.endpoint
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(helpers.endpoint_binding(self.endpoint))

        print 'ack sender endpoint: %s' % self.ack_endpoint
        self.ack_sender = self.context.socket(zmq.PUSH)
        self.ack_sender.bind(helpers.endpoint_binding(self.ack_endpoint))

        self.ack_data = {}

    @abstractmethod
    def handle_collection(self, data, task_type, msgtype):
        """
        Invoked by the collector when data is received from a worker.
        :param data: Data supplied by the worker (a dictionary). If the worker doesn't return anything this will be an empty dict
        :param task_type: The task type of the worker and corresponding task
        :param msgtype: The message type. Typically zmqpipeline.messages.MESSAGE_TYPE_DATA
        :return:
        """
        pass

    def handle_finished(self, data, task_type):
        """
        Invoked by the collector when message
        :param data: Data received from the worker on a termination signal
        :param task_type: The task type of the worker and correspond task
        :return: None
        """
        pass


    def run(self):
        acks_sent = 0
        print 'main loop running'

        while True:
            msg = self.receiver.recv()
            data, task_type, msgtype = messages.get(msg)

            if msgtype == messages.MESSAGE_TYPE_END:
                print 'end message received'
                self.handle_finished(data, task_type)
                break

            self.ack_data = {}
            params = {
                'data': data,
                'task_type': task_type,
                'msgtype': msgtype
            }

            sdata = self.handle_collection(**params)
            if sdata and isinstance(sdata, dict):
                self.ack_data.update(sdata)

            # print 'sending ack %d' % acks_sent
            self.ack_sender.send(messages.create_ack(task_type, self.ack_data))
            acks_sent += 1

