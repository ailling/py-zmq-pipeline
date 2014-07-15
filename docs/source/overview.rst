Overview and features
=====================

Introduction
-------------


Py-zmq-pipeline is as high level pipeline pattern implemented in Python_ with ZeroMQ_.

The `ZeroMQ Pipeline pattern`_ is a data and task distribution pattern for distributed
and parallel computing. The py-zmq-pipeline implementation abstracts away many details of ZeroMQ
while keeping all the performance advantages the framework offers.

This library focuses more on task distribution than data distribution, since
distributing data creates a memory bottleneck and tends not to scale well.

Client workers are responsible for both retrieval and processing of data
in this implementation.


Features
--------


A good pipeline pattern implementation will use load balancing to ensure all workers are supplied
with roughly the same amount of work. While ZeroMQ provides fair-queuing and uniform request distribution
out of the box, it **does not automatically provide load balancing**. Py-zmq-pipeline **does have load balancing**
built in automatically.

Additional features include:

    * Built-in single and multi-threaded workers
    * Task dependencies
        - Allows you to construct dependency trees of tasks
    * Templated design pattern
        - This means you inherit a class, provide your own implementation and invoke a run() method
    * High performance with low overhead (benchmarks available in examples_)
    * Reliability
        - workers can die and be restarted without interrupting overall workflow.
        - repeatedly sent tasks are not re-processed once acknowledged
    * Fast serialization
        - uses msgpack_ for highly efficient, dense and flexible packing of information, allowing py-zmq-pipeline to have a minimal footprint on the wire.
    * Load-balanced
    * Built in logging support for easier debugging

.. _msgpack: http://msgpack.org/
.. _examples: examples.html
.. _`ZeroMQ Pipeline pattern`: http://zguide.zeromq.org/py:all#toc14

Overview
---------

There are 4 components in py-zmq-pipeline:

    * A :ref:`distributor-class`, responsible for pushing registered tasks to worker clients
    * A :ref:`task-class`, an encapsulation of work that needs to be done and configures the distributor to do it
    * A :ref:`worker-class`, a class that consumes computational resources to execute a given task instance
    * A :ref:`collector-class`, a sink that accepts receipts of completed work and sends ACKs (acknowledgements) back to the distributor

Under the server / client paradigm the distributor, task and collector are server-side entities, while the worker is a client entity.

