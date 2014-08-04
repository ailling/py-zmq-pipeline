import logging
from collections import defaultdict

from utils import messages
import helpers

from descriptors import EndpointAddress
import zmq
import uuid


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

        # self.queued_requests = []
        # self.queued_responses = []

        # keyed on a UUID corresponding to the incoming request
        # value - list of multipart messages (which are lists)
        self.queued_requests = {}
        self.sent_requests = defaultdict(list)

        # keyed on a UUID corresponding to the matching request
        # value: list of responses received from the worker
        # when the length of the value
        self.queued_responses = {}

        # keyed on task type, valued on an index of the workers list
        self.task_type_index = {}


    def send_request_to_backend(self):
        for request_id, requests in self.queued_requests.items():
            if requests:
                request = requests.pop()
                self.sent_requests[request_id].append(request)
                self.backend.send_multipart(request)
                return True

        return False


    def queue_request(self, request_id, tt, data, routing_data):
        index = self.task_type_index[tt]

        if isinstance(data, list):
            # round-robin selection of workers
            for item in data:
                worker_id = self.workers_list[tt][index]
                self.queued_requests[request_id].append([
                    worker_id, b'', routing_data, b'', messages.create_data(tt, item)
                ])

                index += 1
                if index % len(self.workers_list[tt]) == 0:
                    index = 0
                self.task_type_index[tt] = index

        else:
            index += 1
            if index % len(self.workers_list[tt]) == 0:
                index = 0
            self.task_type_index[tt] = index

            worker_id = self.workers_list[tt][index]
            self.queued_requests[request_id].append([
                worker_id, b'', routing_data, b'', data
            ])



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

                if msgtype == messages.MESSAGE_TYPE_ROUTING:
                    assert 'address' in data
                    client_addr = data['address']
                    request_id = data['request_id']

                    # empty address
                    self.backend.recv()
                    # get the message
                    msg = self.backend.recv()
                    data, tt, msgtype = messages.get(msg)

                    logger.debug('Routing RESPONSE from worker %s to client %s', worker_addr, client_addr)

                    self.queued_responses[request_id].append(data)

                    if len(self.queued_responses[request_id]) == len(self.sent_requests[request_id]):
                        # TODO: clear the queued requests and responses as well
                        self.frontend.send_multipart([
                            client_addr, b'', messages.create_data(tt, self.queued_responses[request_id])
                        ])



            logger.debug('Workers available: %d', self.available_workers)
            if self.available_workers > 0:

                request_sent = self.send_request_to_backend()

                if self.frontend in socks and socks[self.frontend] == zmq.POLLIN:

                    request_id = str(uuid.uuid1())
                    self.queued_requests[request_id] = []
                    self.queued_responses[request_id] = []
                    self.sent_requests[request_id] = []

                    client_addr, empty, msg = self.frontend.recv_multipart()
                    data, tt, msgtype = messages.get(msg)
                    self.task_type_index.setdefault(tt, 0)

                    routing_data = messages.create_routing(task = tt, data = {
                        'address': client_addr,
                        'request_id': request_id
                    })

                    assert msgtype == messages.MESSAGE_TYPE_DATA
                    assert tt in self.workers_list


                    self.available_workers -= 1
                    logger.debug('Routing task type: %s', tt)
                    logger.debug('Workers list keys: %s', str(self.workers_list.keys()))

                    self.queue_request(request_id, tt, data, routing_data)

                    if not request_sent:
                        self.send_request_to_backend()


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

