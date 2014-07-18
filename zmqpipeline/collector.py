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
        self.metadata = {}

        self._ack_id_counter = 1


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

    def get_ack_data(self):
        """
        Optionally override this method to attach data to the ACK that will be sent back to the distributor.

        This method is typically used when deciding to override Task.is_available_for_handling(), since the data
        received by the distributor will be forwarded to the Task via is_available_for_handling() for
        determining whether the task can be executed or not.

        The use case of implementing these methods in conjuction is for the task to wait on the receipt of a particular
        ACK - that is, if the currently processing ACK requires data from a previously processed result.
        These types of tasks are time and order-dependent.

        :return: A dictionary of data
        """
        return {}


    def run(self):
        """
        Runs the collector. Invoke this method to start the collector

        :return: None
        """
        acks_sent = 0
        ack_id_counter = 1
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

            logger.debug('Invoking handle_collection - task_type: %s msgtype: %s data: %s', task_type, msgtype, data)
            sdata = self.handle_collection(data, task_type, msgtype)
            if not sdata is None and not isinstance(sdata, dict):
                raise TypeError('handle_collection must return a dictionary or none. See documentation')

            ackdata = {
                '_id': ack_id_counter,
                '_task_type': task_type
            }

            ad = self.get_ack_data()
            if not isinstance(ad, dict):
                raise TypeError('get_ack_data() must return a dictionary')

            ackdata.update(ad)
            if sdata:
                ackdata.update(sdata)

            logger.debug('Sending ACK %d to distributor with task type: %s and data: %s', ack_id_counter, task_type, ackdata)
            self.ack_sender.send(messages.create_ack(task_type, ackdata))
            acks_sent += 1
            ack_id_counter += 1

