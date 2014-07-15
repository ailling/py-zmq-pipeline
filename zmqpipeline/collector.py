import logging
from abc import ABCMeta, abstractmethod, abstractproperty
import zmq
from utils import messages
import helpers

logger = logging.getLogger('zmqpipeline.collector')


class CollectorMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        if name != 'Collector':
            pass

        return super(CollectorMeta, cls).__new__(cls, name, bases, dct)



class Collector(object):
    """
    Collects results from the workers and sends ACKs (acknowledgements) back to the distributor
    """
    __metaclass__ = CollectorMeta

    @abstractproperty
    def endpoint(self):
        """
        Endpoint to bind the collector to for receiving messages from workers. Workers should
        connect to this same endpoint for sending data.

        This property must be defined by the subclassed implementation.

        :return: An EndpointAddress instance
        """
        return ''


    @abstractproperty
    def ack_endpoint(self):
        """
        Endpoint for sending ACKs (acknowledgements) back to the distributor. The distributor
        should connect to this same endpoint for receiving ACKs.

        This property must be defined by the sublcassed implementation.

        :return: An EndpointAdress instance
        """
        return ''


    def __init__(self):
        logger.info('Initializing collector')

        self.context = zmq.Context()

        logger.info('Connecting to endpoint %s', self.endpoint)
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(helpers.endpoint_binding(self.endpoint))

        logger.info('Connecting to endpoint %s', self.ack_endpoint)
        self.ack_sender = self.context.socket(zmq.PUSH)
        self.ack_sender.bind(helpers.endpoint_binding(self.ack_endpoint))

        self.ack_data = {}
        self.metadata = {}

    @abstractmethod
    def handle_collection(self, data, task_type, msgtype):
        """
        Invoked by the collector when data is received from a worker.

        :param dict data: Data supplied by the worker (a dictionary). If the worker doesn't return anything this will be an empty dict
        :param str task_type: The task type of the worker and corresponding task
        :param str msgtype: The message type. Typically zmqpipeline.messages.MESSAGE_TYPE_DATA

        :return: None
        """
        pass


    def handle_finished(self, data, task_type):
        """
        Invoked by the collector when message

        :param dict data: Data received from the worker on a termination signal
        :param string task_type: The task type of the worker and correspond task
        :return dict: A dictionary of data to be sent to the distributor along with the ACK, or None to send nothing back to the distributor
        """
        pass


    def run(self):
        """
        Runs the collector. Invoke this method to start the collector

        :return: None
        """
        acks_sent = 0
        logger.info('Collector is running (main loop procesing)')

        while True:
            msg = self.receiver.recv()
            data, task_type, msgtype = messages.get(msg)

            if msgtype == messages.MESSAGE_TYPE_END:
                logger.info('END message received')
                self.handle_finished(data, task_type)
                break

            if msgtype == messages.MESSAGE_TYPE_META_DATA:
                self.metadata = data
                logger.info('Received metadata: %s', self.metadata)
                continue

            self.ack_data = {}
            params = {
                'data': data,
                'task_type': task_type,
                'msgtype': msgtype
            }

            logger.debug('Invoking handle_collection with parameters: %s', params)

            sdata = self.handle_collection(**params)
            if sdata and isinstance(sdata, dict):
                self.ack_data.update(sdata)

            logger.debug('Sending ACK %d to distributor with data: %s', acks_sent, self.ack_data)
            self.ack_sender.send(messages.create_ack(task_type, self.ack_data))
            acks_sent += 1

