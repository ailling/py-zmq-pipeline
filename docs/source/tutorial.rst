Tutorial
==========

This tutorial will walk you through basic concepts of the py-zmq-pipeline library,
using code examples of minimalistic implementaions along the way. For more
realistic examples see the examples_ section.


.. _distributor-class:

Distributor class
-----------------

The distributor class does not need to be inherited from. Its behavior is defined
at instantiation and through the registration of tasks.

The distributor is instantiated as:

.. code-block:: python

    Distributor(collector_endpoint, collector_ack_endpoint, [receive_metadata = False, [metadata_endpoint = None]])

If receive_metadata is True, a metadata endpoint must be provided. In this case the distributor will wait for
metadata to be received until it begins processing tasks, and all metadata will be forwarded to the tasks. Tasks
can then optionally forward metadata to the workers if needed.

All tasks that need to be distributed must be reigstered with the distributor before invoking run():

.. code-block:: python

    Distributor.register_task(MyTask)

Start the distributor with run():

.. code-block:: python

    dist = Distributor(...)
    dist.run()


.. _task-class:

Task class
-----------

The task class is an abstract base class requiring the following implementations:

    * task_type: a valid :ref:`task-type`
        - determines the type of task. Task types must be registered with the TaskType class before the task is declared. See the documentation for :ref:`task-type` for more.
    * endpoint: a valid :ref:`endpoint-address`
        - the endpoint for the worker address. The worker will connect to this endpoint to receive data. See the documentation for :ref:`endpoint-address` for more.
    * dependencies: a list of :ref:`task-types` instances.
        - Dependencies are tasks that must be complete before the given task can be executed
    * handle: invoked by the distributor to determine what information to forward to the worker.
        - Must return either a dictionary or nothing. Other return types, such as list or string, will raise a TypeError.

The signature of the handle() method is:

.. code-block:: python

    @abstractmethod
    def handle(self, data, address, msgtype):
        """
        Handle invocation by the distributor.
        :param data: Meta data, if provided, otherwise an empty dictionary
        :param address: The address of the worker data will be sent to.
        :param msgtype: The message type received from the worker. Typically zmqpipeline.messages.MESSAGE_TYPE_READY
        :return: A dictionary of data to be sent to the worker, or None, in which case the worker will receive no information
        """
        pass


Optionally a task can override initialize() to setup the worker. This is particularly helpful when metadata is supplied.

The default implementation is to store the metadata on the task:

.. code-block:: python

    def initialize(self, metadata={}):
        """
        Initializes the task. Default implementation is to store metadata on the object instance
        :param metadata: Metadata received from the distributor
        :return:
        """
        self.metadata = metadata


A minimal task implementation looks like this:

.. code-block:: python

    import zmqpipeline
    zmqpipeline.TaskType.register_type('MYTSK')

    class MyTask(zmqpipeline.Task):
        task_type = zmqpipeline.TaskType('MYTSK)
        endpoint = zmqpipeline.EndpointAddress('ipc://worker.ipc')
        dependencies = []

        def handle(self, data, address, msgtype):
            """
            Simulates some work to be done
            :param data: Data received from distributor
            :param address: The address of the client where task output will be sent
            :param msgtype: the type of message received. Typically zmqpipeline.utils.messages.MESSAGE_TYPE_DATA
            :return:
            """
            self.n_count += 1
            if self.n_count >= 100:
                # mark as complete after 100 executions.
                self.is_complete = True

            # return the work to be done on the worker
            return {
                'workload': .01
            }



.. _worker-class:

Worker class
-------------

The worker is an abstract base class that requires the following to be defined:

    * task_type: a valid :ref:`task-type`
    * endpoint: a valid :ref:`endpoint-address`
        - the worker will connect to this endpoint to receive tasks from the the distributor
    * collector_endpoint: a valid :ref:`endpoint-address`
        - the worker will connect to this endpoint to send output to. It should be the address of the collector endpoint
    * handle_execution: a method for handling messages from the distributor.

The signature of the handle_execution() method is:

.. code-block:: python

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


You can also optionally define a method: init_worker. By default it has no implementation:

.. code-block:: python

    def init_worker(self):
        pass

This method will be invoked after the worker advertises its availability for the first time and receives a message
back from the distributor. Note that if the worker depends on one or more tasks, it won't receive an acknowledgement
from the distributor and hence this method will not be invoked until after those dependent tasks have finished processing.


.. _single-worker-class:

SingleThreadedWorker class
~~~~~~~~~~~~~~~~~~~~~~~~

The single threaded worker is a pure implementation of the :ref:`worker-class` documented above.


.. _multi-worker-class:

MultiThreadedWorker class
~~~~~~~~~~~~~~~~~~~~~~~~~

The multi threaded worker implements the :ref:`worker-class` documented above but requires two pieces of information:

    * handle_thread_execution(): method for handling data forwarded by the worker.
        - this is where data processing should take place in the multi threaded worker
    * n_threads: the number of threads to utilize in the worker. Should be a positive integer.

being processed in handle_execution, work is intended to be handled by handle_thread_execution().

You must still implement handle_execution(), but its role is to forward data to the thread, possibly
making modificiations or doing pre-processing before hand.

The signature of handle_thread_execution() is:

.. code-block:: python

    @abstractmethod
    def handle_thread_execution(self, data, index):
        """
        Invoked in worker's thread. Override in client implementation
        :return:
        """
        return {}


A minimal implementation of the multi threaded worker is:

.. code-block:: python

    import zmqpipeline
    import time
    zmqpipeline.TaskType.register_type('MYTSK')

    class MyWorker(zmqpipeline.MultiThreadedWorker):
        task_type = zmqpipeline.TaskType('MYTSK')
        endpoint = zmqpipeline.EndpointAddress('ipc://worker.ipc')
        collector_endpoint = zmqpipeline.EndpointAddress('ipc://collector.ipc')

        n_threads = 10
        n_executions = 0

        def handle_execution(self, data, *args, **kwargs):
            """
            Handles execution of the main worker
            :param data:
            :param args:
            :param kwargs:
            :return:
            """
            # forward all received data to the thread
            self.n_executions += 1
            return data


        def handle_thread_execution(self, data, index):
            workload = data['workload']
            time.sleep(workload)

            # returning nothing forwards no extra information to the collector



.. _meta-worker-class:
MetaDataWorker Class
-----------------------

Despite its name, MetaDataWorker doesn't inherit from the Worker base class.

It's a stand-alone abstract base class requiring the following implementations:

    * endpoint: a valid :ref:`endpoint-address` instance
        - this is the address of the meta data worker and should be supplied to the distributor at instantiation when using meta data.
    * get_metadata(): a method returning a dictionary of meta data

The signature of get_metadata() is:

.. code-block:: python

    @abstractmethod
    def get_metadata(self):
        """
        Retrieves meta data to be sent to tasks and workers.
        :return: A dictionary of meta data
        """
        return {}

A typical use case for retrieving meta data is querying a database or introspecting live code.

To start the meta data worker, call the run() method. A minimal implementation of a meta data worker is provided below.

.. code-block:: python

    import zmqpipeline

    class MyMetaData(zmqpipeline.MetaDataWorker):
        endpoint = zmqpipeline.EndpointAddress('ipc://metaworker.ipc')

        def get_metadata(self):
            """
            Returns meta data for illustrative purposes
            :return:
            """
            return {
                'meta_variable': 'my value',
            }

    if __name__ == '__main__':
        instance = MyMetaData()
        instance.run()


.. _collector-class:

Collector class
----------------

The collector is an abstract base class requiring implementations of the following:

    * endpoint: a valid :ref:`endpoint-address`
    * ack_endpoint: a valid :ref:`endpoint-address`
    * handle_collection: a method to handle messages received by the worker

The signature of handle_collection() is:

.. code-block:: python

    @abstractmethod
    def handle_collection(self, data, task_type, msgtype):
        """
        Invoked by the collector when data is received from a worker.
        :param data: Data supplied by the worker (a dictionary). If the worker doesn't return anything this will be an empty dict
        :param task_type: The task type of the worker and corresponding task
        :param msgtype: The message type. Typically zmqpipeline.messages.MESSAGE_TYPE_DATA
        :return:
        """
        pass

You can optionally implement handle_finished(), which is invoked when the collector receives a termination signal from the distributor.

The signature of handle_finished() is:

.. code-block:: python

    def handle_finished(self, data, task_type):
        """
        Invoked by the collector when message
        :param data: Data received from the worker on a termination signal
        :param task_type: The task type of the worker and correspond task
        :return: None
        """
        pass


.. _endpoint-address:

Endpoint address
---------------

A string that must be a valid endpoint address, otherwise a type error is thrown.

Endpoint address signature:

.. code-block:: python

    zmqpipeline.EndpointAddress(string)

Addresses must belong to one of the acceptable protocols to be considered valid. Accepted protocols are:

    * tpc
    * ipc
    * inproc

tpc should be used for connecting code across machines. ipc (inter-process-communication) can be used for
connecting two apps on the same machine. inproc can only be used for connecting threads to a process.
It is significantly faster than tpc or ipc and used by default in the multi threaded worker.

.. _task-type:

Task type
------------

A string that identifies a task and a worker. Tasks and workers specify a task type in one-to-one fashion.
That is, one task type can be associated with one task and one worker. No more, no less.
This allows zmqpipeline to coordinate tasks and workers.

Task types can be any valid string but must be registered with zmqpipeline before using them declaratively.

To register a task type:

.. code-block:: python

    zmqpipeline.TaskType.register_type('MY_TASK_TYPE')

You can now use this type as follows:

.. code-block:: python

    task_type = zmqpipeline.TaskType('MY_TASK_TYPE')

.. _messages:

Messages
--------------

Messages are stand-alone data structures used by zmqpipeline internally for packing additional
information along with the data being put on the wire. You shouldn't be interacting with the messages library
directly - documentation is provided here for debugging purposes only.

.. _message-type:

Message type
~~~~~~~~~~~~~~

Message types are defined in zmqpipeline.utils.messages

The available message types are:

.. code-block:: text

    * MESSAGE_TYPE_ACK: acknowledgement
    * MESSAGE_TYPE_SUCCESS: success
    * MESSAGE_TYPE_FAILURE: failure
    * MESSAGE_TYPE_READY: ready
    * MESSAGE_TYPE_END: termination
    * MESSAGE_TYPE_DATA: data
    * MESSAGE_TYPE_META_DATA: metadata
    * MESSAGE_TYPE_EMPTY: empty message

.. _create-messages:

Creating messages
~~~~~~~~~~~~~~~~~

Message signatures are defined as follows:

.. code-block:: python

    def create(data, tasktype, msgtype):
    def create_data(task, data):
    def create_metadata(metadata):
    def create_ack(task = '', data=''):
    def create_success(task = '', data=''):
    def create_failure(task = '', data=''):
    def create_empty(task = '', data=''):
    def create_ready(task = '', data=''):
    def create_end(task = '', data=''):

