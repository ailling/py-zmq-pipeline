import settings
from zmqpipeline import TaskType, ServiceClient


N_REQUESTS = 2

if __name__ == '__main__':
    client = ServiceClient(settings.FRONTENT_ENDPOINT, task_type = TaskType(settings.TASK_TYPE_MY_TASK))

    for i in range(N_REQUESTS):
        print 'client issuing request'
        reply = client.request({
            'message': 'hello'
        })
        print 'client received reply: %s' % str(reply)


    # ls = [{
    #     'message': 'hello 1',
    # }, {
    #     'message': 'hello 2'
    # }]
    #
    # reply = client.request(ls)
    # print 'received reply: ', reply

    print 'finished'

