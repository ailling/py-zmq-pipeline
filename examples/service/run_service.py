import settings
from zmqpipeline.service import Service
from zmqpipeline import EndpointAddress



if __name__ == '__main__':
    service = Service(
        frontend_endpoint = EndpointAddress(settings.FRONTENT_ENDPOINT),
        backend_endpoint = EndpointAddress(settings.BACKEND_ENDPOINT)
    )

    print 'running service'
    service.run()

    print 'finished'

