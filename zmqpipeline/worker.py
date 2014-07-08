from abc import ABCMeta, abstractmethod, abstractproperty

from utils import messages
from descriptors import TaskType, EndpointAddress

import zmq
import zhelpers
import helpers
from threading import Thread


class WorkerMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        if name not in ('Worker', 'MultiThreadedWorker', 'SingleThreadedWorker'):
            if not isinstance(dct['task_type'], TaskType):
                raise TypeError('task_type is required to be a TaskType enumerated value')

            if not isinstance(dct['endpoint'], EndpointAddress):
                raise TypeError('endpoint is required to be an EndpointAddress object')

            if not isinstance(dct['collector_endpoint'], EndpointAddress):
                raise TypeError('collector_endpoint is requiredto be an EndpointAddress object')

            slots = []
            for key, value in dct.items():
                if isinstance(value, EndpointAddress):
                    value.name = '_' + key
                    slots.append(value.name)
                dct['__slots__'] = slots

        return super(WorkerMeta, cls).__new__(cls, name, bases, dct)



class Worker(object):
    __metaclass__ = WorkerMeta

    @abstractproperty
    def task_type(self):
        return None

    @abstractproperty
    def endpoint(self):
        return ''

    @abstractproperty
    def collector_endpoint(self):
        return ''

    def __init__(self, *args, **kwargs):
        self.context = zmq.Context()
        print 'worker will send to collector endpoint: %s' % self.collector_endpoint
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.connect(self.collector_endpoint)

        print 'worker connecting to endpoint %s' % self.endpoint
        self.worker = self.context.socket(zmq.REQ)
        zhelpers.set_id(self.worker)
        self.worker.connect(self.endpoint)

        print 'worker id: %s' % self.worker.getsockopt(zmq.IDENTITY)


    def send_init_msg(self):
        print 'sending init message to %s' % self.endpoint
        self.worker.send(b'')
        self.worker.recv_multipart()

        print 'received reply - initializing worker'

        initfn = getattr(self, 'init_worker', None)
        if initfn and callable(initfn):
            initfn()


    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def main_loop(self):
        pass

    def init_worker(self):
        pass



class MultiThreadedWorker(Worker):
    thread_endpoint = EndpointAddress('inproc://threadworker')

    @abstractproperty
    def n_threads(self):
        return 1

    def __init__(self, *args, **kwargs):
        super(MultiThreadedWorker, self).__init__(*args, **kwargs)

        self.thread_router = self.context.socket(zmq.REP)
        self.thread_router.bind(helpers.endpoint_binding(self.thread_endpoint))


    def worker_thread(self, worker_index, context):
        w = context.socket(zmq.REQ)
        zhelpers.set_id(w)
        w.connect(self.thread_endpoint)

        initfn = getattr(self, 'init_thread', None)
        if initfn and callable(initfn):
            initfn(worker_index = worker_index)


        while True:
            w.send(messages.create_ready())

            msg = w.recv()
            data, tt, msgtype = messages.get(msg)

            assert tt == self.task_type

            if msgtype == messages.MESSAGE_TYPE_END:
                break

            data = data or {}
            sdata = self.handle_thread_execution(data = data, index = worker_index)
            if sdata:
                data.update(sdata)
            smsg = messages.create_data(self.task_type, data)
            self.sender.send(smsg)



    def init_threads(self):
        for i in range(self.n_threads):
            Thread(target = self.worker_thread, args=[i, self.context]).start()

    def shutdown_threads(self):
        for _ in range(self.n_threads):
            self.thread_router.recv()
            self.thread_router.send(messages.create_end(task = self.task_type))


    def main_loop(self):
        print 'main loop running'

        while True:
            print 'sending ready message'
            self.worker.send(messages.create_ready(self.task_type))

            msg = self.worker.recv()
            print 'received reply'

            data, tt, msgtype = messages.get(msg)

            assert tt == self.task_type

            if msgtype == messages.MESSAGE_TYPE_END:
                print 'received end message'
                self.shutdown_threads()
                print 'threads are shutdown'
                break

            self.thread_router.recv()
            data = data or {}
            sdata = self.handle_execution(data) or {}
            self.thread_router.send(messages.create_data(self.task_type, sdata))


    def run(self):
        self.init_threads()
        self.send_init_msg()
        self.main_loop()


    @abstractmethod
    def handle_execution(self, data, *args, **kwargs):
        """
        Invoked in the worker's main loop. Override in client implementation
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        return {}


    @abstractmethod
    def handle_thread_execution(self, data, index):
        """
        Invoked in worker's thread. Override in client implementation
        :return:
        """
        return {}



class SingleThreadedWorker(Worker):

    def main_loop(self):
        print 'worker - main loop running'

        while True:
            # print 'sending ready message'

            self.worker.send(messages.create_ready(self.task_type))

            msg = self.worker.recv()
            # print 'received reply'

            data, tt, msgtype = messages.get(msg)

            assert tt == self.task_type

            if msgtype == messages.MESSAGE_TYPE_END:
                print 'received end message'
                break

            data = data or {}
            sdata = self.handle_execution(data) or {}
            smsg = messages.create_data(self.task_type, sdata)
            self.sender.send(smsg)


    def run(self):
        self.send_init_msg()
        self.main_loop()


    @abstractmethod
    def handle_execution(self, data, *args, **kwargs):
        """
        Invoked in the worker's main loop. Override in client implementation
        :param data: Data provided as a dictionary from the distributor
        :param args:
        :param kwargs:
        :return: A dictionary of data to be passed to the collector, or None, in which case no data will be forwarded to the collector
        """
        return {}



class MetaDataWorker(object):
    """
    Transmits algorithm meta information
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def endpoint(self):
        return ''

    def __init__(self):
        self.context = zmq.Context()
        self.worker = self.context.socket(zmq.REQ)
        zhelpers.set_id(self.worker)
        self.worker.connect(self.endpoint)

    def send_metadata(self):
        # metadata = quantnode.Calculator.GetImplementationMetadata()
        metadata = self.get_metadata()
        print 'sending metadata'
        self.worker.send(messages.create_metadata(metadata))

        # sent metadata - wait for reply
        self.worker.recv()
        print 'metadata reply received'


    def run(self):
        self.send_metadata()


    @abstractmethod
    def get_metadata(self):
        return {}

