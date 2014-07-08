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

