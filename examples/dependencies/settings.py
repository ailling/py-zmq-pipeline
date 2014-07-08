##################################################
# PUT ZMQPIPELINE LIBRARY ON SYSTEM PATH
##################################################

import os, sys

app_path = os.path.dirname(os.path.abspath(__file__))
examples_path = os.path.join(app_path, '..')
root_path = os.path.join(examples_path, '..')

if root_path not in sys.path:
    sys.path.insert(0, root_path)


##################################################
# APP SETTINGS
##################################################


import zmqpipeline


TASK_TYPE_FIRST = '1'
TASK_TYPE_SECOND = '2'

zmqpipeline.TaskType.register_type(TASK_TYPE_FIRST)
zmqpipeline.TaskType.register_type(TASK_TYPE_SECOND)

COLLECTOR_ENDPOINT = 'tcp://localhost:5558'
COLLECTOR_ACK_ENDPOINT = 'tcp://localhost:5551'
FIRST_WORKER_ENDPOINT = 'ipc://firstworker.ipc'
SECOND_WORKER_ENDPOINT = 'ipc://secondworker.ipc'

METADATA_ENDPOINT = 'ipc://metadata.ipc'

