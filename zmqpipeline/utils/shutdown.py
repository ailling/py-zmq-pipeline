import os
import signal

def kill_current_process():
    """
    Kills the current process. Unix only.
    :return:
    """
    pid = os.getpid()
    os.kill(pid, signal.SIGKILL)

