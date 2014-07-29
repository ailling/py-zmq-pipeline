import logging

import zmq
import zhelpers
import helpers

from utils import messages
from descriptors import TaskType, EndpointAddress

N_MESSAGES = 5

class ServiceClient(object):

    endpoint = EndpointAddress('tcp://localhost:15201')
    id_prefix = 'client'

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.client_id = zhelpers.set_id(self.socket, prefix=self.id_prefix)
        self.socket.connect(self.endpoint)


    def run(self):

        while True:

            req = {
                'message': 'hello'
            }
            print 'client %s sending message: %s' % (self.client_id, str(req))

            msg = messages.create_data('', data=req)
            self.socket.send(msg)

            reply = self.socket.recv()
            response, tt, msgtype = messages.get(reply)

            print 'client %s received response: %s' % (self.client_id, str(response))

        print 'client %s finished' % self.client_id

