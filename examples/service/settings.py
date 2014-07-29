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


