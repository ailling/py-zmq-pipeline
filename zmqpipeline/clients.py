import logging

import zmq
import zhelpers

from utils import messages
from descriptors import TaskType, EndpointAddress

logger = logging.getLogger('zmqpipeline.serviceclient')


class ServiceClient(object):

    def __init__(self, endpoint_address, task_type = '', id_prefix = 'client'):
        """
        Instantiates a sevice client.

        :param EndpointAddress endpoint_address: Address of the service broker's frontend
        :param TaskType task_type: A registered task type or a blank string. Can be overridden in the request
        :param str id_prefix: A prefix for the id of the client, useful for debugging
        :return: A ServiceClient instance
        """

        if not endpoint_address:
            raise TypeError('Must supply an endpoint address')

        if not isinstance(endpoint_address, EndpointAddress):
            endpoint_address = EndpointAddress(endpoint_address)

        self.task_type = ''
        if task_type:
            if not isinstance(task_type, TaskType):
                raise TypeError('task_type is required to be a TaskType enumerated value')

            self.task_type = task_type

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.client_id = zhelpers.set_id(self.socket, prefix=id_prefix)
        logger.debug('Client id: %s', self.client_id)

        if endpoint_address:
            self.endpoint = EndpointAddress(endpoint_address)

        logger.info('Client connecting to endpoint: %s', endpoint_address)
        self.socket.connect(self.endpoint)



    def request(self, data, task_type=''):
        """
        Issues a request to the service broker. The service broker is asynchronous but this call is blocking.

        :param data: Data to be passed to the worker. This can be a dictionary for a single worker invocation or a
            list of dictionaries to distribute work in parallel.
        :param TaskType task_type: valid registered TaskType instance or an empty string
        :return: The response from the workers
        """
        if not task_type:
            task_type = self.task_type
        if task_type and not isinstance(task_type, TaskType):
            raise TypeError('task_type must be a TaskType enumerated value, or a blank string')

        msg = messages.create_data(task_type, data = data)
        logger.debug('Client %s sending request for task %s', self.client_id, task_type)
        self.socket.send(msg)
        reply = self.socket.recv()

        response, tt, msgtype = messages.get(reply)
        logger.debug('Client %s received reply for task type %s, msgtype: %s, response: %s',
                     self.client_id, tt, msgtype, str(response)
        )

        return response

