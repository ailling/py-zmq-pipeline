from utils import messages
import helpers

from descriptors import EndpointAddress
from task import Task

import zmq


class Distributor(object):
    task_classes = {}

    def __init__(self, collector_endpoint, collector_ack_endpoint,
                 receive_metadata = False, metadata_endpoint = None):
        self.context = zmq.Context()
        self.metadata = {}

        if not isinstance(collector_endpoint, EndpointAddress):
            raise TypeError('collector_endpoint must be an EndpointAddress instance')
        if not isinstance(collector_ack_endpoint, EndpointAddress):
            raise TypeError('collector_ack_endpoint must be an EndpointAddress instance')

        self.sink = self.context.socket(zmq.PUSH)
        # self.sink.connect(consts.COLLECTOR_ENDPOINT)
        self.sink.connect(collector_endpoint)

        self.sink_ack = self.context.socket(zmq.PULL)
        # self.sink_ack.connect(consts.COLLECTOR_ACK_ENDPOINT)
        self.sink_ack.connect(collector_ack_endpoint)

        if receive_metadata:
            if not metadata_endpoint:
                raise AttributeError('metadata_endpoint is required to receive metadata')
            if not isinstance(metadata_endpoint, EndpointAddress):
                raise TypeError('metadata_endpoint must be an EndpointAddress instance')

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
        print 'waiting to receive metadata'
        
        msg = self.metadata_client.recv()
        data, task, msgtype = messages.get(msg)
        assert msgtype == messages.MESSAGE_TYPE_META_DATA
        assert task == messages.TASK_TYPE_NA

        print 'storing metadata: ', data
        if data:
            self.metadata = data
            for tt, task in self.tasks.items():
                if hasattr(task, 'initialize'):
                    task.initialize(metadata = self.metadata)

        self.metadata_client.send(messages.create_success())


    def process_sink_ack(self):
        msg = self.sink_ack.recv()
        data, tt, msgtype = messages.get(msg)

        self.tasks[tt].n_acks += 1
        # print 'acks: %d' % self.tasks[tt].n_acks


    def register_task_instance(self, taskcls):
        print 'registering task class: ', taskcls
        task = taskcls()

        print 'binding endpoint %s' % task.endpoint
        s = self.context.socket(zmq.ROUTER)
        s.bind(helpers.endpoint_binding(task.endpoint))

        task.client = s
        self.clients[task.task_type] = s
        self.tasks[task.task_type] = task
        Task.register_task_instance(task)
        self.poller.register(s, zmq.POLLIN)

    def add_client_address(self, task_type, addr):
        if task_type not in self.client_addresses:
            self.client_addresses[task_type] = set()
        self.client_addresses[task_type].add(addr)


    def run(self):
        print 'main loop running'

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
                        print 'initial signal for task %s from worker %s received' % (task, address)
                        self.worker_initialized[address] = True
                        task.received_init_signal = True

                        print 'sending success reply'
                        task.client.send_multipart([
                            address, b'', messages.create_success(task = task_type)
                        ])

                    else:
                        data, tt, msgtype = messages.get(msg)

                        if msgtype == messages.MESSAGE_TYPE_READY:
                            "invoke the registered function"
                            sdata = task.handle(data, address, msgtype) or {}
                            if not isinstance(sdata, dict) and sdata is not None:
                                raise TypeError('Task handler must return a dictionary or nothing')

                            task.client.send_multipart([
                                address, b'', messages.create_data(tt, sdata)
                            ])

        # shutdown collector + workers
        self.shutdown()


    def shutdown(self):
        print 'sending END message to sink'
        self.sink.send(messages.create_end())

        for task_type, task in self.tasks.items():
            print 'shutting down clients for task %s' % task_type

            client_addrs = self.client_addresses[task_type]
            n_clients = len(client_addrs)
            print 'shutting down %d clients' % n_clients
            for _ in client_addrs:
                address, empty, msg = task.client.recv_multipart()
                task.client.send_multipart([
                    address, b'', messages.create_end(task = task_type)
                ])


