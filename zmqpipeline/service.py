import logging
from collections import defaultdict

from utils import messages
import helpers

from descriptors import EndpointAddress
import zmq
import uuid
import pdb


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

        self.backend = self.context.socket(zmq.PUSH)
        self.backend.bind(helpers.endpoint_binding(self.backend_endpoint))

        self.init_socket = self.context.socket(zmq.ROUTER)
        self.init_socket.bind(helpers.endpoint_binding('tcp://localhost:16001'))

        self.ack_socket = self.context.socket(zmq.PULL)
        self.ack_socket.bind(helpers.endpoint_binding('tcp://localhost:16002'))

        self.poller = zmq.Poller()
        self.poller.register(self.ack_socket, zmq.POLLIN)
        self.poller.register(self.init_socket, zmq.POLLIN)
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        self.workers_list = defaultdict(list)
        self.available_workers = 0

        # keyed on a UUID corresponding to the incoming request
        # value - list of multipart messages (which are lists)
        self.queued_requests = {}
        self.processing_requests = defaultdict(list)

        # keyed on request id, valued on the number of requests
        self.n_requests = {}
        self.n_acks = {}

        # keyed on a UUID corresponding to the matching request
        # value: list of responses received from the worker
        # when the length of the value
        self.queued_responses = {}

        # keyed on task type, valued on an index of the workers list
        self.task_type_index = {}


    def send_request_to_backend(self):
        """
        Sends a queued request to the backend if one exists
        :return: True if a task was sent, false otherwise (no task is waiting to be sent)
        """
        for request_id, requests in self.queued_requests.items():
            if requests:
                request = requests.pop()
                self.processing_requests[request_id].append(request)
                # self.backend.send_multipart(request)

                tt = request['task_type']
                index = self.task_type_index[tt]
                worker_id = self.workers_list[tt][index]

                self.backend.send_multipart([
                    worker_id, b'', request['routing_data'], b'', request['data']
                ])

                index += 1
                if index % len(self.workers_list[request['task_type']]) == 0:
                    index = 0
                self.task_type_index[tt] = index

                return True

        return False


    # def send_all_requests_to_backend(self):
    #     raise NotImplementedError()
    #     for request_id, requests in self.queued_requests.items():
    #         while len(requests) > 0:
    #             request = requests.pop()
    #             self.backend.send_multipart(request)


    def queue_request(self, request_id, tt, data, routing_data):
        """
        Queues requests to be sent without assigning a worker (done later to distribute work to newly arriving workers)
        """
        # index = self.task_type_index[tt]
        self.n_acks[request_id] = 0

        if isinstance(data, list):
            self.n_requests[request_id] = len(data)

            # round-robin selection of workers
            for item in data:
                # worker_id = self.workers_list[tt][index]
                # self.queued_requests[request_id].append([
                #     worker_id, b'', routing_data, b'', messages.create_data(tt, item)
                # ])

                self.queued_requests[request_id].append({
                    'routing_data': routing_data,
                    'data': messages.create_data(tt, item),
                    'task_type': tt
                })

                # index += 1
                # if index % len(self.workers_list[tt]) == 0:
                #     index = 0
                # self.task_type_index[tt] = index

        else:
            self.n_requests[request_id] = 1

            # index += 1
            # if index % len(self.workers_list[tt]) == 0:
            #     index = 0
            # self.task_type_index[tt] = index

            # worker_id = self.workers_list[tt][index]
            # self.queued_requests[request_id].append([
            #     worker_id, b'', routing_data, b'', data
            # ])

            self.queued_requests[request_id].append({
                'routing_data': routing_data,
                'data': data,
                'task_type': tt
            })



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

            if self.ack_socket in socks and socks[self.ack_socket] == zmq.POLLIN:

                msg = self.ack_socket.recv()
                data, tt, msgtype = messages.get(msg)
                routing_data = data['routing_data']
                request_id = routing_data['request_id']

                response = data['response']

                # addr, empty, msg = self.ack_socket.recv_multipart()
                # data = messages.get(msg)
                # request_id = data['request_id']

                self.n_acks[request_id] += 1
                self.queued_responses[request_id].append(response)
                print 'received ACK from worker - n: %d' % self.n_acks[request_id]

                if self.n_acks[request_id] == self.n_requests[request_id]:
                    # all requests have finished processing, send message to the client
                    self.frontend.send_multipart([
                        client_addr, b'', messages.create_success(tt, self.queued_responses)
                    ])
                else:
                    self.send_request_to_backend()


            if self.init_socket in socks and socks[self.init_socket] == zmq.POLLIN:

                worker_addr = self.init_socket.recv()

                # the empty frame
                self.init_socket.recv()

                clientmsg = self.init_socket.recv()
                data, tt, msgtype = messages.get(clientmsg)
                self.available_workers += 1
                self.workers_list[tt].append(worker_addr)


            if self.backend in socks and socks[self.backend] == zmq.POLLIN:
                raise NotImplementedError()

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

                    logger.debug('*** N requests: %d responses: %d', self.n_requests[request_id], len(self.queued_responses[request_id]))
                    if len(self.queued_responses[request_id]) == self.n_requests[request_id]:
                        # TODO: clear the queued requests and responses
                        self.frontend.send_multipart([
                            client_addr, b'', messages.create_data(tt, self.queued_responses[request_id])
                        ])


            # logger.debug('Workers available: %d', self.available_workers)
            if self.available_workers > 0:

                if self.frontend in socks and socks[self.frontend] == zmq.POLLIN:

                    request_id = str(uuid.uuid1())
                    self.queued_requests[request_id] = []
                    self.queued_responses[request_id] = []
                    self.processing_requests[request_id] = []
                    self.n_acks[request_id] = 0
                    self.n_requests[request_id] = 0

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

                    # self.send_all_requests_to_backend()
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

