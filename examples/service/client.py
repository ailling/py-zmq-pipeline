import settings
from zmqpipeline import TaskType, ServiceClient


N_REQUESTS = 10

if __name__ == '__main__':
    client = ServiceClient(settings.FRONTENT_ENDPOINT, task_type = TaskType(settings.TASK_TYPE_MY_TASK))

    # for i in range(N_REQUESTS):
    #     print 'client issuing request'
    #     reply = client.request({
    #         'message': 'hello'
    #     })
    #     print 'client received reply: %s' % str(reply)


    ls = []
    for i in range(N_REQUESTS):
        ls.append({
            'message': 'hello %d' % i
        })

    reply = client.request(ls)
    print 'received reply: ', reply

    print 'finished'

