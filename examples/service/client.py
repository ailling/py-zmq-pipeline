import settings
from zmqpipeline.clients import ServiceClient


if __name__ == '__main__':
    client = ServiceClient()

    print 'running client'
    client.run()

    print 'finished'

