import settings
import zmqpipeline

class MyCollector(zmqpipeline.Collector):
    endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)
    ack_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ACK_ENDPOINT)

    def handle_collection(self, data, task_type, msgtype):
        pass

if __name__ == '__main__':
    collector = MyCollector()
    print 'collector running'
    collector.run()

    print 'finished'
