import settings
import zmqpipeline
import time

class StopWatchCollector(zmqpipeline.Collector):
    endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ENDPOINT)
    ack_endpoint = zmqpipeline.EndpointAddress(settings.COLLECTOR_ACK_ENDPOINT)

    start_time = None
    end_time = None

    @property
    def total_msec(self):
        if not self.end_time or not self.start_time:
            return 0

        return (self.end_time - self.start_time) * 1000

    def handle_collection(self, data, task_type, msgtype):
        if not self.start_time:
            self.start_time = time.time()


    def handle_finished(self, data, task_type):
        self.end_time = time.time()
        print 'collection took %.1f milliseconds' % self.total_msec


if __name__ == '__main__':
    collector = StopWatchCollector()
    print 'collector running'
    collector.run()

    print 'finished'
