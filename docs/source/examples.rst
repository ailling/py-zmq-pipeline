Examples
========

.. highlight:: python
.. role:: python(code)
   :language: python


These examples will illustrate using py-zmq-pipeline by distributing a workload to one or more workers.
We'll sleep 10 milliseconds to simulate some work being done.

The examples covered are:

    * :ref:`example-1` will provide a baseline how quickly a workload can be executed
    * :ref:`example-2` will illustrate using a basic worker and compare performance to the baseline
    * :ref:`example-3` will illustrate using the multi threaded worker and compare performance
    * :ref:`example-4` will illustrate how to construct tasks that depend on each other
    * :ref:`example-5` will illustrate how to use metadata to start the distributor

Machine specs are more or less irrelevant for the amount of work being simulated, but for the record
these benchmarks were made on a 4 core Intel i7 processor with 8GB of ram, running Linux Mint 16.


.. _example-1:

Example 1: Sequential execution
-------------------------------

This example is used to establish a benchmark for future tests.

In examples/sequential/benchmark.py::

    import time

    def main(n, delay):
        print 'running - iterations: %d - delay: %.3f' % (n, delay)

        start = time.time()

        for i in xrange(n):
            time.sleep(delay)

        m = (time.time() - start) * 1000
        expected = n * delay * 1000
        overhead = m / expected - 1.0
        print 'expected execution time: %.1f' % expected
        print 'sequential execution took: %.1f milliseconds' % m
        print 'overhead: %.1f%%' % (overhead * 100.0)

    if __name__ == '__main__':
        main(100, .01)
        main(1000, .01)
        main(5000, .01)

Produces the following output:

.. code-block:: text

    running - iterations: 100 - delay: 0.010
    expected execution time: 1000.0
    sequential execution took: 1011.5 milliseconds
    overhead: 1.2%
    running - iterations: 1000 - delay: 0.010
    expected execution time: 10000.0
    sequential execution took: 10112.4 milliseconds
    overhead: 1.1%
    running - iterations: 5000 - delay: 0.010
    expected execution time: 50000.0
    sequential execution took: 50522.6 milliseconds
    overhead: 1.0%

This benchmark establishes an overhead of about 1% for seqeuntially looping over a piece of work. The overhead
is due to looping the for loop, maintaining an index, calling the generator, as well as measurement errors in the time() method.

If we observe, say a 5% overhead in future benchmarks, we're really taking about a 4% difference from the benchmark.

.. _example-2:

Example 2: Single threaded worker
---------------------------------

As explained in the overview_, there are 4 components in py-zmq-pipeline:

    * Distributor, responsible for pushing registered tasks to worker clients
    * Task, an encapsulation of work that needs to be done and configures the distributor to do it
    * Worker, a class that consumes computational resources to execute a given task instance
    * Collector, a sink that accepts receipts of completed work and sends ACKs (acknowledgements) back to the distributor

Under the server / client paradigm the distributor, task and collector are server-side entities, while the worker is a client entity.

.. _overview: overview.html

First let's setup some settings for the app. In examples/singlethread/settings.py::

    ##################################################
    # PUT ZMQPIPELINE LIBRARY ON SYSTEM PATH
    ##################################################
    import os, sys

    app_path = os.path.dirname(os.path.abspath(__file__))
    examples_path = os.path.join(app_path, '..')
    root_path = os.path.join(examples_path, '..')

    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    ##################################################
    # APP SETTINGS
    ##################################################
    import zmqpipeline

    TASK_TYPE_CALC = 'C'
    zmqpipeline.TaskType.register_type(TASK_TYPE_CALC)

    COLLECTOR_ENDPOINT = 'tcp://localhost:5558'
    COLLECTOR_ACK_ENDPOINT = 'tcp://localhost:5551'
    WORKER_ENDPOINT = 'ipc://worker.ipc'

The first part of this file is just adding py-zmq-pipeline to the command line in case you decided to clone
the project and you're running it from within the examples directory. It will be common to all settings files in subsequent examples.

In the app settings section we're defining a task type and registering it with the library.
Tasks are associated with task types in one-to-one fashion and should represent a unit of isolated work to be done.
Some task types may depend on one or more other types; we'll cover that in example 4.


Let's write the task to issue some work. In examples/singlethread/tasks.py::

    import settings
    import zmqpipeline

    class CalculationTask(zmqpipeline.Task):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_CALC)
        endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
        dependencies = []
        n_count = 0

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
                # mark as complete after 1000 executions. Should take a total of 10 seconds to run sequentially
                self.is_complete = True

            # return the work to be done on the worker
            return {
                'workload': .01
            }

The distributor invokes a method on the task called handle(). This method should supply details about the work
to be done and return it as a dictionary. That dictionary will be forwarded to the worker by the distributor.

Workers receive work by advertising their availability to the distributor. At that time the worker provides
its address and message type. Message types are available in the API reference_. The data parameter will typically
be an empty dictionary; it will likely be used in future versions.

Finally, the task controls how much work to send, in this case 100 messages.

.. _reference: reference.html

Here's an implementation of the worker, in examples/singlethread/worker.py::

    import settings
    import zmqpipeline
    from zmqpipeline.utils import shutdown
    import time

    class MyWorker(zmqpipeline.SingleThreadedWorker):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_CALC)
        endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
        collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

        n_executions = 0

        def handle_execution(self, data, *args, **kwargs):
            self.n_executions += 1

            workload = data['workload']
            time.sleep(workload)

            # returning nothing forwards no extra information to the collector

    if __name__ == '__main__':
        worker = MyWorker()
        print 'worker running'
        worker.run()

        print 'finished - handled %d executions' % worker.n_executions
        shutdown.kill_current_process()

The single threaded worker must provide an implementation of handle_execution(). This method is invoked whenever
data is received from the distributor. The contents of data is determined by the task corresponding to the worker's task_type.

In this worker implementation we keep track of the number of executions made by the worker. py-zmq-pipeline uses
implements a load balancing pattern, so if there are M total tasks and N workers are started, each worker
should be executed approximately M/N times.

Note that the worker's job to receive input and deliver output. It receives input from the distributor, the connection
to which is listed as WORKER_ENDPOINT in the settings module. It delivers output to the collector, connected to by the
collector_endpoint address.

Next we have to implement the collector. In examples/singlethread/collector.py::

    import settings
    import zmqpipeline
    import time

    class StopWatchCollector(zmqpipeline.Collector):
        endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)
        ack_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ACK_ENDPOINT)

        start_time = None
        end_time = None

        @property
        def total_msec(self):
            if not self.end_time or not self.start_time:
                return 0

            return (self.end_time - self.start_time) * 1000

        def handle_collection(self, data, task_type, msgtype):
            if not self.start_time:
                self.start_time = time.time()


        def handle_finished(self, data, task_type, msgtype):
            self.end_time = time.time()
            print 'collection took %.1f milliseconds' % self.total_msec


    if __name__ == '__main__':
        collector = StopWatchCollector()
        print 'collector running'
        collector.run()

        print 'finished'

This collector acts as a simple stopwatch in order to assess the performance of the worker. handle_collection()
is invoked whenever the collector receives data from a worker, and handle_finished() is invoked whenever
the distributor sends a termination message. The collector automatically sends ACKs (acknowledgements) back to the
distributor, but needs to be explicitly setup with the ack_endpoint address. The endpoint address is used to communicate
with workers.

Note that every message from a worker is sent back to the distributor as an ACK. Due to the frequency of messages
traveling from collector to distributor it's best to put the collector and distributor on the same machine, posssibly
connected through the ipc protocol instead of tcp.

Finally setting up and running the distributor is simple. All tasks need to be registered with the distributor before
instantiating it and collector endpoint addresses are provided to the constructor. In examples/singlethread/run_distributor.py::

    import settings
    import zmqpipeline
    import tasks

    if __name__ == '__main__':
        zmqpipeline.Distributor.register_task(tasks.CalculationTask)

        dist = zmqpipeline.Distributor(
            collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT),
            collector_ack_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ACK_ENDPOINT)
        )
        dist.run()
        print 'finished'

Normally the distributor, collector and workers can be started in any order. For this example, make sure to start
the collector first otherwise the output of the stopwatch might not make sense.

Single threaded worker benchmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Running the above example yields the following.

    * One worker
        - 100 tasks: 1060 milliseconds (6% overhead)
        - 1000 tasks: 10850 milliseconds (8.5% overhead)
        - 5000 tasks: 53940 milliseconds (7.8% overhead)
    * Two workers
        - 100 tasks: 527 milliseconds (5.4% overhead)
        - 1000 tasks: 550 milliseconds (10% overhead)
        - 5000 tasks: 26900 milliseconds (7.6% overhead)

As expected, the overhead is slightly higher for more workers since there's now a greater coordination burden
by the distributor. However, while doubling the number of workers reduces the total processing time by a 2X order
of maginitude, the overhead doesn't change much. The load balancing implementation is well worth the expense.


.. _example-3:

Example 3: Multi threaded worker
---------------------------------

Switching from a single threaded to a multi threaded worker is a matter of inherint from a different subclass::

    import settings
    import zmqpipeline
    from zmqpipeline.utils import shutdown
    import time

    class MyWorker(zmqpipeline.MultiThreadedWorker):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_CALC)
        endpoint = zmqpipeline.EndpointAddress(settings.WORKER_ENDPOINT)
        collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

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

    if __name__ == '__main__':
        worker = MyWorker()
        print 'worker running'
        worker.run()

        print 'finished - handled %d executions' % worker.n_executions
        shutdown.kill_current_process()

A multithreaded worker requires you to implement two methods: handle_execution() and handle_thread_execution().
The former forwards data to the thread executor. In this example, we're not adding any data to what's received by the worker
and simply making a note that the worker was executed. This time, the thread execution simulates the work as before.

Multi threaded worker benchmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    * One worker, 10 threads
        - 100 tasks: 93 milliseconds (7% **gain**)
        - 1000 tasks: 1070 milliseconds (7% overhead)
        - 5000 tasks: 5430 milliseconds (8.6% overhead)
    * Two workers, 10 threads per worker
        - 100 tasks: 51 milliseconds (2% overhead)
        - 1000 tasks: 560 milliseconds (12% overhead)
        - 5000 tasks: 2818 milliseconds (12.7% overhead)

Notice that with 100 tasks that take 10 milliseconds each running on 10 parallel threads would expect
to take 100 total milliseconds to run. The benchmark with a single worker actually shows a gain over the
expected processing time. This means the time it takes it pull 100 messages off the wire and relay it to the
thread is less than 10 milliseconds, even though the threads themselves are load balanced. It works only for the
low-volume case because the worker is able to pull a relatively large percentage of the workload (10%) at one time.

.. _example-4:

Example 4: Task dependencies
---------------------------------

This example is similar to the single threaded worker example, except we now have two tasks: FirstTask
and SecondTask. We require that FirstTask be executed before SecondTask.

The tasks are defined in examples/dependencies/tasks.py::

    import settings
    import zmqpipeline

    class FirstTask(zmqpipeline.Task):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_FIRST)
        endpoint = zmqpipeline.EndpointAddress(settings.FIRST_WORKER_ENDPOINT)
        dependencies = []
        n_count = 0

        def handle(self, data, address, msgtype):
            """
            Simulates some work to be done
            :param data:
            :param address:
            :param msgtype:
            :return:
            """
            self.n_count += 1
            if self.n_count >= 500:
                # mark as complete after 1000 executions. Should take a total of 10 seconds to run sequentially
                self.is_complete = True

            # return the work to be done on the worker
            return {
                'workload': .01
            }


    class SecondTask(zmqpipeline.Task):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_SECOND)
        endpoint = zmqpipeline.EndpointAddress(settings.SECOND_WORKER_ENDPOINT)
        dependencies = [zmqpipeline.TaskType(settings.TASK_TYPE_FIRST)]
        n_count = 0

        def handle(self, data, address, msgtype):
            """
            Simulates some work to be done
            :param data:
            :param address:
            :param msgtype:
            :return:
            """
            self.n_count += 1
            if self.n_count >= 500:
                # mark as complete after 1000 executions. Should take a total of 10 seconds to run sequentially
                self.is_complete = True

            # return the work to be done on the worker
            return {
                'workload': .01
            }

Notice the dependencies variable is provided as a list of task types, each type corresponding to a particular worker.
This means we'll need two different workers to handle the task types.

The first worker is defined in examples/dependencies/first_worker.py::

    import settings
    import zmqpipeline
    from zmqpipeline.utils import shutdown
    import time

    class FirstWorker(zmqpipeline.SingleThreadedWorker):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_FIRST)
        endpoint = zmqpipeline.EndpointAddress(settings.FIRST_WORKER_ENDPOINT)
        collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

        n_executions = 0

        def handle_execution(self, data, *args, **kwargs):
            self.n_executions += 1

            workload = data['workload']
            print 'first worker - working for %f seconds' % workload
            time.sleep(workload)

            # returning nothing forwards no extra information to the collector

    if __name__ == '__main__':
        worker = FirstWorker()
        print 'worker running'
        worker.run()

        print 'finished - handled %d executions' % worker.n_executions
        shutdown.kill_current_process()

The second worker is defined in examples/dependencies/second_worker.py::

    import settings
    import zmqpipeline
    from zmqpipeline.utils import shutdown
    import time

    class SecondWorker(zmqpipeline.SingleThreadedWorker):
        task_type = zmqpipeline.TaskType(settings.TASK_TYPE_SECOND)
        endpoint = zmqpipeline.EndpointAddress(settings.SECOND_WORKER_ENDPOINT)
        collector_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)

        n_executions = 0

        def handle_execution(self, data, *args, **kwargs):
            self.n_executions += 1

            workload = data['workload']
            print 'second worker - working for %f seconds' % workload
            time.sleep(workload)

            # returning nothing forwards no extra information to the collector

    if __name__ == '__main__':
        worker = SecondWorker()
        print 'worker running'
        worker.run()

        print 'finished - handled %d executions' % worker.n_executions
        shutdown.kill_current_process()


Running this example you'll see the output of the second worker commence only when the first worker is finished
processing all of its tasks.


.. _example-5:

Example 5: Using metadata
---------------------------------

This example is forthcoming.
