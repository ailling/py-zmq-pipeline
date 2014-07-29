import settings
from zmqpipeline.service import Service


if __name__ == '__main__':
    service = Service()

    print 'running service'
    service.run()

    print 'finished'

