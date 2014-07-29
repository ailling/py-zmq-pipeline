import os, sys, subprocess, time, unittest
sys.path.insert(0, os.path.abspath('..'))
import signal
from factories.distributor import DistributorFactory


def server_distributor():
    dist = DistributorFactory.build()
    dist.run()


def server():
    try:
        for _ in xrange(5, 0, -1):
            print 'ding'
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # pid = os.getpid()
    # print 'child pid: ', pid
    # os.kill(pid, signal.SIGKILL)


class TestClient(unittest.TestCase):
    def setUp(self):
        self.server_pid = None
        pid = os.fork()
        if not pid:
            # child
            # return dist.run()
            # return server()
            return server_distributor()

        # parent
        self.server_pid = pid

    def test1(self):
        print 'test server, PID ', self.server_pid
        print 'running test - sleeping for 5 seconds'
        time.sleep(5)

    def tearDown(self):
        if not self.server_pid:
            return
        import signal
        print 'killing pid: ', self.server_pid
        os.kill(self.server_pid, signal.SIGKILL)

