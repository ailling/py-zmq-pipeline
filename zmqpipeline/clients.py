import logging

import zmq
import zhelpers
import helpers

from utils import messages
from descriptors import TaskType, EndpointAddress

N_MESSAGES = 5

class ServiceClient(object):

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.client_id = zhelpers.set_id(self.socket, prefix='Client')
        self.socket.connect('tcp://localhost:15201')

        self.initialized = False
        self.init_sent = False

        self.counter = 0

    def run(self):

        while True:

            req = {
                'message': 'hello'
            }
            print 'client %s sending message: %s' % (self.client_id, str(req))

            msg = messages.create_data('', data=req)
            self.socket.send(msg)

            self.counter += 1
            if self.counter > N_MESSAGES:
                break

            reply = self.socket.recv()
            response, tt, msgtype = messages.get(reply)

            print 'client %s received response: %s' % (self.client_id, str(response))

        print 'client %s finished' % self.client_id

