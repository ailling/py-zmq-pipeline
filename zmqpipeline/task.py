from abc import ABCMeta, abstractproperty, abstractmethod
from descriptors import TaskType, EndpointAddress
from collections import defaultdict
import logging

logger = logging.getLogger('zmqpipeline.task')


class TaskMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        if name != 'Task':
            if not isinstance(dct['task_type'], TaskType):
                raise TypeError('task_type is required to be a TaskType enumerated value')

            if not isinstance(dct['endpoint'], EndpointAddress):
                raise TypeError('endpoint is required to be an EndpointAddress instance')

            if not isinstance(dct['dependencies'], list):
                raise TypeError('dependencies must be a list')

            deps = dct['dependencies']
            for dep in deps:
                if not isinstance(dep, TaskType):
                    raise TypeError('Each item in dependencies must be a TaskType enumerated value')

        return type.__new__(cls, name, bases, dct)



class Task(object):
    """
    Tasks define what information the workers receive at each invocation as well as how many items
    to be processed.

    Tasks dynamically configure the Distributor, which looks up and invokes registered tasks.

    """
    __metaclass__ = TaskMeta
    n_items = 0
    n_acks = 0
    n_sent = 0
    received_init_signal = False
    client_addresses = set()
    client = None
    is_complete = False
    metadata = {}
    task_instances = defaultdict(list)


    def is_available_for_handling(self, last_ack_data):
        """
        Optionally override this if the task requires the ACK of a previously sent task.

        If this method is overriden, get_ack_data() should be overrridden in your custom collector.
        The default is to always assume the task is available to process the next task. This is the fastest
        behavior, but also doesn't guarantee the last message sent by the task (and then the corresponding worker)
        has been ACKed by the distributor.

        :param dict last_ack_data: A dictionary of data received in the last ACK. All instances include _task_type and _id, a globally incrementing counter for the latest ACK.
            This dictionary will include whatever you attach to get_ack_data() in the collector. If you override this method, you should override get_col
        :return: True if the task is available for handling the next received message; false if otherwise
        """
        return True


    @classmethod
    def register_task_instance(cls, instance):
        cls.task_instances[instance.task_type].append(instance)

    @abstractproperty
    def task_type(self):
        """
        The type of task being defined. This type must be registered with TaskType before definition,
        otherwise an exception will be thrown

        :return: A TaskType instance
        """
        pass

    @abstractproperty
    def endpoint(self):
        """
        A valid EndpointAddress used to push data to worker clients.

        :return: An EndpointAddress instance
        """
        pass

    @abstractproperty
    def dependencies(self):
        """
        Zero or more tasks, identified by task type, that must be executed in full before this task can begin processing.

        :return: A list of TaskType instances
        """
        return []

    def initialize(self, metadata={}):
        """
        Initializes the task. Default implementation is to store metadata on the object instance
        :param metadata: Metadata received from the distributor
        :return:
        """
        logger.debug('Initializing task with meta data %s', metadata)
        self.metadata = metadata

    @abstractmethod
    def handle(self, data, address, msgtype, ack_data={}):
        """
        Handle invocation by the distributor.

        :param dict data: Meta data, if provided, otherwise an empty dictionary
        :param EndpointAddress address: The address of the worker data will be sent to.
        :param str msgtype: The message type received from the worker. Typically zmqpipeline.messages.MESSAGE_TYPE_READY
        :param dict ack_data: Data received in the most recent ACK from collector
        :return dict: A dictionary of data to be sent to the worker, or None, in which case the worker will receive no information
        """
        pass


    def is_task_ready_for_initialization(self):
        if self.is_complete or self.received_init_signal:
            # if complete or already received an init signal, it cannot be initialized
            return False

        deps = self.dependencies
        if not deps:
            # if no dependency, it's ready for init + processing
            return True
        else:
            # otherwise, all dependencies must be complete
            for dep in deps:
                if any([not i.is_complete for i in Task.task_instances[dep]]):
                    return False
            return True

