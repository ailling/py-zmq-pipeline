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

TASK_TYPE_MY_TASK = 'MYTSK'
zmqpipeline.TaskType.register_type(TASK_TYPE_MY_TASK)

FRONTENT_ENDPOINT = 'tcp://localhost:15101'
BACKEND_ENDPOINT = 'tcp://localhost:15102'



zmqpipeline.configureLogging({
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        # console logger
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'zmqpipeline.service': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'zmqpipeline.serviceworker': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'zmqpipeline.serviceclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
})

