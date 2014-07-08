import sys
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

install_requires = [
    'argparse >= 1.2.1',
    'msgpack-python >= 0.4.2',
    'pyzmq >= 14.3.1',
    'wsgiref >= 0.1.2',
    'py >= 1.4.20',
    'pytest >= 2.5.2',
    'pytz >= 2014.4'
]

long_description = ''
with open('description.txt', 'rb') as f:
    long_description = f.read()

def get_version():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zmqpipeline'))
    from version import VERSION
    v = VERSION
    sys.path.pop(0)
    return v


setup(
    name='py-zmq-pipeline',
    version=get_version(),
    description='High level implementation of the pipeline task distribution pattern with ZeroMQ',
    long_description=long_description,
    author='Alan Illing',
    author_email='',
    url='https://github.com/ailling/py-zmq-pipeline',
    packages=['zmqpipeline', 'zmqpipeline.utils'],
    package_data={'zmqpipeline': ['../VERSION', '../description.txt']},
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
