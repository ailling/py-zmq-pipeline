import settings
from zmqpipeline.clients import ServiceClient

N_REQUESTS = 10

if __name__ == '__main__':
    client = ServiceClient(settings.FRONTENT_ENDPOINT)

    for i in range(N_REQUESTS):
        print 'client issuing request'
        reply = client.request({
            'message': 'hello'
        })
        print 'client received reply: %s' % str(reply)

    print 'finished'

