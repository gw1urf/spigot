# Usage:
#
# lm = LoadManager(max_queue_len = 10, target_pcpu = 50)
#
# # Inside a bunch of threads:
# with lm:
#   do_some_heavy_processing()
#
# This will permit only a single thread to call do_some_heavy_processing,
# and, on exit from the context, a time.sleep() will be called to enforce
# an overall average CPU usage over the "with" elapsed time.
#
# If more than max_queue_len threads are waiting for the lock, then the
# queue.Full exception will be raised. Setting max_queue_len to zero
# effectively sets an infinite queue.
#   
import queue
import threading
import time

class LoadManager:
    def __init__(self, max_queue_len=0, target_pcpu=100):
        self.lock = threading.Lock()
        self.queue = queue.Queue(max_queue_len)
        self.target_pcpu = target_pcpu

    def __enter__(self):
        self.queue.put(1, block=False)
        self.lock.acquire()
        self.start_time = time.time()

    def __exit__(self, type, value, traceback):
        elapsed = time.time() - self.start_time
        sleeptime = elapsed*100/self.target_pcpu - elapsed
        if sleeptime > 0:
            time.sleep(sleeptime)
        self.lock.release()
        self.queue.get()

    def waiting(self):
        return self.queue.qsize()
