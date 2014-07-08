Installation
=============

Install from PyPI
------------------

Run the following from your terminal or GitBash_ (for windows users) to install from PyPI_::

    pip install zmqpipeline



.. _PyPI: https://pypi.python.org/pypi
.. _GitBash: http://msysgit.github.io/


Install from source
--------------------

Clone the git repository::

    git clone git@github.com/ailling/py-zmq-pipeline.git

Install::

    cd py-zmq-pipeline
    python setup.py install

In both cases it's recommended you install into a virtual environment using virtualenv_ or virtualenvwrapper_.

.. _virtualenv: http://virtualenv.readthedocs.org/en/latest/
.. _virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/

Test installation
-----------------

You should now be able to import zmqpipeline from your Python interpreter::

    >>> import zmqpipeline


Running tests
--------------

py-zmq-pipeline uses pytest_ for running tests. It is included in the installation of py-zmq-pipeline.

To run the tests::

    py.test tests


.. _pytest: http://pytest.org/latest/
