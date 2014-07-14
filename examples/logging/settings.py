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
# EXAMPLE LOGGING SETTINGS
# reference: https://docs.python.org/2/library/logging.html
##################################################
import zmqpipeline
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
        # a file handler
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'output.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'zmqpipeline.distributor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'zmqpipeline.task': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'zmqpipeline.collector': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'zmqpipeline.worker': {
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

# MORE: https://docs.python.org/2/library/logging.html
