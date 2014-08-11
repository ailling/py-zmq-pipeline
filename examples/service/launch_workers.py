import worker
import subprocess
import atexit

import psutil
import os, sys
import signal
import pdb

N_WORKERS = 1
WORKER_PIDS = []
CHILD_WORKER_PIDS = []


def launch_worker():
    return subprocess.Popen("/home/alan/workspace/py-zmq-pipeline/venv/bin/python /home/alan/workspace/py-zmq-pipeline/examples/service/worker.py", shell=True)


def main():
    print 'pid: ', os.getpid()
    print 'parent pid: ', os.getppid()

    for i in range(N_WORKERS):
        proc = launch_worker()
        WORKER_PIDS.append(proc.pid)
        print 'launched: %d' % proc.pid
        ps = psutil.Process(proc.pid)
        print 'children:'
        for child in ps.get_children():
            CHILD_WORKER_PIDS.append(child.pid)


@atexit.register
def kill_workers():
    for pid in WORKER_PIDS:
        print 'killing %d' % pid
        os.kill(pid, signal.SIGKILL)

    for pid in CHILD_WORKER_PIDS:
        print 'killing CHILD %d' % pid
        os.kill(pid, signal.SIGKILL)


if __name__ == '__main__':
    main()
    print 'Press ENTER to exit'
    raw_input()

    print 'killing workers'
    kill_workers()
    print 'exiting'

