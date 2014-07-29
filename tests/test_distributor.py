from factories.distributor import DistributorFactory, COLLECTOR_ACK_ENDPOINT, COLLECTOR_ENDPOINT
import os, sys, subprocess, time, unittest
import signal
import time


def test_instantiation():
    DistributorFactory.build()
    dist = DistributorFactory.create()
    assert True


def server():
    try:
        for _ in xrange(5, 0, -1):
            print 'ding'
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def test_run():
    server_pid = None
    pid = os.fork()
    if not pid:
        # child
        return server()

    server_pid = pid
    print 'sleeping for 5 seconds'
    time.sleep(5)
    os.kill(server_pid, signal.SIGINT)



# class TestClient(unittest.TestCase):
#     def setUp(self):
#         self.server_pid = None
#         dist = DistributorFactory.build()
#         pid = os.fork()
#         if not pid:             # child
#             return dist.run()
#         # parent
#         self.server_pid = pid
#
#     def test1(self):
#         print 'test server, PID', self.server_pid
#         time.sleep(5)
#
#     def tearDown(self):
#         if not self.server_pid:
#             return
#         import signal
#         print 'tearing down distributor'
#         os.kill(self.server_pid, signal.SIGINT)


