from collector import Collector
from descriptors import EndpointAddress, TaskType
from distributor import Distributor
from task import Task
from worker import SingleThreadedWorker, MultiThreadedWorker, MetaDataWorker, ServiceWorker
from service import Service
from clients import ServiceClient


def configureLogging(config):
    import logging
    import logging.config
    logging.config.dictConfig(config)

