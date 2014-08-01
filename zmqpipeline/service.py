import logging
from collections import defaultdict

from utils import messages
import helpers

from descriptors import EndpointAddress
import zmq

logger = logging.getLogger('zmqpipeline.service')


class Service(object):
    """
    A service is a load-balanced router, accepting multiple client requests asynchronously
    and distributing the work to multiple workers.
    """
    task_classes = {}

    def __init__(self, frontend_endpoint, backend_endpoint):
        if not frontend_endpoint:
            raise TypeError('Must provide a valid frontend endpoint')
        if not isinstance(frontend_endpoint, EndpointAddress):
            frontend_endpoint = EndpointAddress(frontend_endpoint)

        if not backend_endpoint:
            raise TypeError('Must provide a valid backend endpoint')
        if not isinstance(backend_endpoint, EndpointAddress):
            backend_endpoint = EndpointAddress(backend_endpoint)

        self.frontend_endpoint = frontend_endpoint
        self.backend_endpoint = backend_endpoint

        logger.info('Initializing service')
        self.context = zmq.Context()

        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(helpers.endpoint_binding(self.frontend_endpoint))

        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(helpers.endpoint_binding(self.backend_endpoint))

        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        self.workers_list = defaultdict(list)
        self.available_workers = 0

        self.queued_requests = []
        self.queued_responses = []


    def run(self):
        """
        Runs the service. This is a blocking call.

        Since this method will block the calling program, it should be the last thing the calling code
        does before exiting. run() will automatically shutdown the service gracefully when finished.

        :return: None
        """
        logger.info('Service is running (main loop processing)')

        while True:
            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break

            if self.backend in socks and socks[self.backend] == zmq.POLLIN:

                # TODO: collect responses in fragments, issue response to the frontend when complete
                worker_addr = self.backend.recv()

                # the empty frame
                self.backend.recv()

                clientmsg = self.backend.recv()
                data, tt, msgtype = messages.get(clientmsg)
                self.available_workers += 1
                self.workers_list[tt].append(worker_addr)


                logger.debug('Received message from worker id: %s - tt: %s - msgtype: %s', worker_addr, tt, msgtype)

                # if msgtype == messages.MESSAGE_TYPE_DATA:
                #     self.queued_responses.append(data)

                if msgtype == messages.MESSAGE_TYPE_ROUTING:
                    assert 'address' in data
                    client_addr = data['address']

                    # empty address
                    self.backend.recv()
                    # get the message
                    msg = self.backend.recv()
                    data, tt, msgtype = messages.get(msg)

                    self.queued_responses.append(data)

                    logger.debug('Routing RESPONSE from worker %s to client %s', worker_addr, client_addr)

                    # TODO: make this code flexible

                    # this is for BATCHED requests (2 = batch size in this case)
                    # if len(self.queued_responses) == 2:
                    #     self.frontend.send_multipart([
                    #         client_addr, b'', messages.create_data(tt, self.queued_responses)
                    #     ])

                    # this is for SINGLE requests
                    self.frontend.send_multipart([
                        client_addr, b'', msg
                    ])


            logger.debug('Workers available: %d', self.available_workers)
            if self.available_workers > 0:
                if self.queued_requests:
                    request = self.queued_requests.pop()
                    self.backend.send_multipart(request)

                if self.frontend in socks and socks[self.frontend] == zmq.POLLIN:

                    client_addr, empty, msg = self.frontend.recv_multipart()
                    data, tt, msgtype = messages.get(msg)
                    routing_data = messages.create_routing(task = tt, data = {
                        'address': client_addr
                    })

                    assert msgtype == messages.MESSAGE_TYPE_DATA
                    assert tt in self.workers_list

                    self.available_workers -= 1
                    logger.debug('Routing task type: %s', tt)
                    logger.debug('Workers list keys: %s', str(self.workers_list.keys()))

                    worker_id = self.workers_list[tt].pop()

                    if isinstance(data, list):
                        # self.backend.send_multipart([
                        #     worker_id, b'', routing_data, b'', data[0]
                        # ])
                        self.backend.send_multipart([
                            worker_id, b'', routing_data, b'', messages.create_data(tt, data[0])
                        ])

                        for item in data[1:]:
                            self.queued_requests.append([
                                worker_id, b'', routing_data, b'', messages.create_data(tt, item)
                            ])

                    else:
                        logger.debug('Routing REQUEST from client %s to worker %s', client_addr, worker_id)
                        self.backend.send_multipart([
                            worker_id, b'', routing_data, b'', msg
                        ])


        # shutdown workers
        self.shutdown()



    def shutdown(self):
        """
        Shuts down the service. This is automatically called when run() is complete and the distributor
        exits gracefully. Client code should only invoke this method directly on exiting prematurely,
        for example on a KeyboardInterruptException

        :return: None
        """
        all_workers = []
        for tt, workers in self.workers_list.items():
            for w in workers:
                all_workers.append(w)

        all_workers = set(all_workers)
        logger.info('Shutting down %d workers', len(all_workers))

        for worker_id in all_workers:
            logger.debug('Shutting down worker id %s', worker_id)

            self.backend.send_multipart([
                worker_id, b'', b'', b'', messages.create_end()
            ])

