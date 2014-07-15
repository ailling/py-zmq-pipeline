import logging

from utils import messages
import helpers

from descriptors import EndpointAddress
from task import Task
import zmq

logger = logging.getLogger('zmqpipeline.distributor')

class Distributor(object):
    """
    Responsible for distributing (pushing) tasks to workers. What gets distributed is determined
    by Tasks, which are user-implementations that configure how the distributor works.

    The pipeline pattern assumes there is only one distributor with one or more registered tasks.
    """
    task_classes = {}

    def __init__(self, collector_endpoint, collector_ack_endpoint,
                 receive_metadata = False, metadata_endpoint = None):
        """
        Instantiate a distributor.

        :param EndpointAddress collector_endpoint: The endpoint of the collector
        :param EndpointAddress collector_ack_endpoint: The endpoint of the collector for receiving ACKs
        :param bool receive_metadata: When true, the distributor will wait for meta data from a meta data worker before distributing tasks to clients
        :param EndpointAddress metadata_endpoint: The endpoint from which to receive meta data from a meta data worker.
        :return: A Distributor object
        """
        logger.info('Initializing distributor')
        self.context = zmq.Context()
        self.metadata = {}

        if not isinstance(collector_endpoint, EndpointAddress):
            raise TypeError('collector_endpoint must be an EndpointAddress instance')
        if not isinstance(collector_ack_endpoint, EndpointAddress):
            raise TypeError('collector_ack_endpoint must be an EndpointAddress instance')

        logger.info('Connecting to collector endpoint %s', collector_endpoint)
        self.sink = self.context.socket(zmq.PUSH)
        self.sink.connect(collector_endpoint)

        logger.info('Connecting to collector ACK endpoint %s', collector_ack_endpoint)
        self.sink_ack = self.context.socket(zmq.PULL)
        self.sink_ack.connect(collector_ack_endpoint)

        if receive_metadata:
            logger.debug('Setting up receiving metadata')
            if not metadata_endpoint:
                raise AttributeError('metadata_endpoint is required to receive metadata')
            if not isinstance(metadata_endpoint, EndpointAddress):
                raise TypeError('metadata_endpoint must be an EndpointAddress instance')

            logger.info('Connecting to meta data worker endpoint %s', metadata_endpoint)
            self.metadata_client = self.context.socket(zmq.REP)
            self.metadata_client.bind(metadata_endpoint)
        else:
            self.metadata_client = None

        self.poller = zmq.Poller()
        self.poller.register(self.sink_ack, zmq.POLLIN)

        self.client_addresses = {}

        # keyed on worker ids
        self.worker_initialized = {}
        self.clients = {}
        self.tasks = {}

        for taskcls in self.registered_task_classes:
            self.register_task_instance(taskcls)

        self.receive_metadata = receive_metadata
        if receive_metadata:
            self.wait_for_metadata()


    @property
    def registered_task_classes(self):
        return self.task_classes.values()


    @classmethod
    def register_task(cls, task):
        if task.task_type not in cls.task_classes:
            cls.task_classes[task.task_type] = task


    def wait_for_metadata(self):
        logger.info('Waiting to receive metadata')
        msg = self.metadata_client.recv()
        data, task, msgtype = messages.get(msg)
        assert msgtype == messages.MESSAGE_TYPE_META_DATA
        assert task == ''

        logger.debug('Storing metadata: %s', data)

        if data:
            self.metadata = data
            for tt, task in self.tasks.items():
                if hasattr(task, 'initialize'):
                    logger.info('Initializing task type %s', task.task_type)
                    task.initialize(metadata = self.metadata)

        logger.info('Meta data received - sending success response')
        self.metadata_client.send(messages.create_success())


    def process_sink_ack(self):
        msg = self.sink_ack.recv()
        data, tt, msgtype = messages.get(msg)

        self.tasks[tt].n_acks += 1
        logger.debug('Received %d acks from task type %s', self.tasks[tt].n_acks, tt)


    def register_task_instance(self, taskcls):
        task = taskcls()
        logger.debug('Registering Task with type %s', task.task_type)

        logger.info('Connecting task type %s to endpoint %s', task.task_type, task.endpoint)
        s = self.context.socket(zmq.ROUTER)
        s.bind(helpers.endpoint_binding(task.endpoint))

        task.client = s
        self.clients[task.task_type] = s
        self.tasks[task.task_type] = task

        logger.debug('Registering task %s', task.task_type)
        Task.register_task_instance(task)
        self.poller.register(s, zmq.POLLIN)


    def add_client_address(self, task_type, addr):
        if task_type not in self.client_addresses:
            self.client_addresses[task_type] = set()
        if addr not in self.client_addresses[task_type]:
            logger.info('Adding new client address: %s for task type: %s', addr, task_type)

        self.client_addresses[task_type].add(addr)


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

            if self.sink_ack in socks:
                self.process_sink_ack()

            alltasks = self.tasks.values()
            if all([t.is_complete for t in alltasks]):
                "exit main loop if all registered tasks are complete"
                logger.info('All tasks complete - exiting distributor main loop')
                break

            for task_type, task in self.tasks.items():
                if task.is_complete:
                    # task finished - skip
                    continue

                if task.is_task_ready_for_initialization() or task.received_init_signal:
                    # task either needs to be initialized, or has been initialized and is ready for processing
                    address, empty, msg = task.client.recv_multipart()
                    self.add_client_address(task_type, address)

                    if not self.worker_initialized.get(address):
                        logger.debug('Initial signal for task %s from worker %s recieved', task_type, address)
                        self.worker_initialized[address] = True
                        task.received_init_signal = True

                        logger.debug('Sending success reply to worker address: %s', address)
                        task.client.send_multipart([
                            address, b'', messages.create_success(task = task_type)
                        ])

                    else:
                        data, tt, msgtype = messages.get(msg)
                        data = data or {}
                        if self.metadata:
                            data.update(self.metadata)

                        if msgtype == messages.MESSAGE_TYPE_READY:
                            "invoke the registered function"
                            logger.debug('Invoking task.handle for task type: %s, client address %s - passing data: %s', task.task_type, address, data)
                            sdata = task.handle(data, address, msgtype) or {}
                            if not isinstance(sdata, dict) and sdata is not None:
                                raise TypeError('Task handler must return a dictionary or nothing')

                            sdata.update(data)

                            logger.debug('Send to collector - task type: %s - data: %s', tt, sdata)
                            task.client.send_multipart([
                                address, b'', messages.create_data(tt, sdata)
                            ])

        # shutdown collector + workers
        self.shutdown()


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

