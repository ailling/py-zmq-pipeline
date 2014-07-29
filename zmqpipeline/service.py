import logging

from utils import messages
import helpers

from descriptors import EndpointAddress
from task import Task
import zmq

logger = logging.getLogger('zmqpipeline.service')


class Service(object):
    """
    A service is a load-balanced router, accepting multiple client requests asynchronously
    and distributing the work to multiple workers.

    """
    task_classes = {}

    frontend_endpoint = EndpointAddress('tcp://localhost:15201')
    backend_endpoint = EndpointAddress('tcp://localhost:15202')

    def __init__(self):
        logger.info('Initializing distributor')
        self.context = zmq.Context()

        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(helpers.endpoint_binding(self.frontend_endpoint))

        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(helpers.endpoint_binding(self.backend_endpoint))

        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        self.workers_list = []
        self.available_workers = 0


    def run(self):
        """
        Runs the distributor and blocks. Call this immediately after instantiating the distributor.

        Since this method will block the calling program, it should be the last thing the calling code
        does before exiting. Run() will automatically shutdown the distributor gracefully when finished.

        :return: None
        """
        logger.info('Distributor is running (main loop processing)')

        while True:
            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break

            if self.backend in socks and socks[self.backend] == zmq.POLLIN:

                worker_addr = self.backend.recv()

                self.available_workers += 1
                self.workers_list.append(worker_addr)

                # the empty frame
                self.backend.recv()

                clientmsg = self.backend.recv()
                data, task, tt = messages.get(clientmsg)

                if tt == messages.MESSAGE_TYPE_UNKNOWN:
                    # unknown message types are because the client sent their address
                    client_addr = clientmsg

                    # this is a client reply - receive an empty frame
                    self.backend.recv()

                    msg = self.backend.recv()

                    self.frontend.send_multipart([
                        client_addr, b'', msg
                    ])


            if self.available_workers > 0:

                if self.frontend in socks and socks[self.frontend] == zmq.POLLIN:

                    client_addr, empty, data = self.frontend.recv_multipart()

                    self.available_workers -= 1
                    worker_id = self.workers_list.pop()

                    self.backend.send_multipart([
                        worker_id, b'', client_addr, b'', data
                    ])


        # shutdown workers
        # self.shutdown()


    def shutdown(self):
        """
        Shuts down the distributor. This is automatically called when run() is complete and the distributor
        exits gracefully. Client code should only invoke this method directly on exiting prematurely,
        for example on a KeyboardInterruptException

        :return: None
        """
        logger.info('Shutting down collector and workers')

        logger.debug('Sending END signal to collector')
        self.sink.send(messages.create_end())

        for task_type, task in self.tasks.items():
            client_addrs = self.client_addresses[task_type]
            n_clients = len(client_addrs)

            logger.debug('Shutting down %d clients for task type %s', n_clients, task_type)
            for _ in client_addrs:
                address, empty, msg = task.client.recv_multipart()

                logger.debug('Sending END signal to worker address %s - task type %s', address, task_type)
                task.client.send_multipart([
                    address, b'', messages.create_end(task = task_type)
                ])

