import settings
import zmqpipeline
from zmqpipeline.utils.shutdown import kill_current_process

class MyMetaData(zmqpipeline.MetaDataWorker):
    endpoint = zmqpipeline.EndpointAddress(settings.METADATA_ENDPOINT)

    def get_metadata(self):
        """
        Returns meta data for illustrative purposes
        :return:
        """
        return {
            'meta_variable': 'my value',
        }

if __name__ == '__main__':
    instance = MyMetaData()
    instance.run()

    print 'worker is finished'
    kill_current_process()

