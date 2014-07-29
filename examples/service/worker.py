import settings
from zmqpipeline.worker import ServiceWorker


if __name__ == '__main__':
    worker = ServiceWorker()

    print 'running worker'
    worker.run()

    print 'finished'

