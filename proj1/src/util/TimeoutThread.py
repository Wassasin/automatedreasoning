import threading
import os
import errno

from contextlib import contextmanager


SIGKILL = 9


class TimeoutThread(object):
    def __init__(self, seconds):
        self.seconds = seconds
        self.cond = threading.Condition()
        self.cancelled = False
        self.thread = threading.Thread(target=self._wait)

    def run(self):
        self.thread.start()

    def _wait(self):
        with self.cond:
            self.cond.wait(self.seconds)

            if not self.cancelled:
                self.timed_out()

    def cancel(self):
        with self.cond:
            self.cancelled = True
            self.cond.notify()
        self.thread.join()

    def timed_out(self):
        raise NotImplementedError


class KillProcessThread(TimeoutThread):
    def __init__(self, seconds, pid):
        super(KillProcessThread, self).__init__(seconds)
        self.pid = pid

    def timed_out(self):
        try:
            os.killpg(self.pid, SIGKILL)
        except OSError as e:
            # If the process is already gone, ignore the error.
            if e.errno not in (errno.EPERM, errno. ESRCH):
                raise e


@contextmanager
def processTimeout(seconds, pid):  # NOQA, pylint: disable=C0103
    timeout = KillProcessThread(seconds, pid)
    timeout.run()
    try:
        yield
    finally:
        timeout.cancel()
