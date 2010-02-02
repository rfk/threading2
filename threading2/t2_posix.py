
from t2_base import *
from t2_base import __all__

import errno
from ctypes import *
from ctypes.util import find_library

libc = find_library("pthread")
if libc is None:
    raise ImportError("libc not found")
libc = CDLL(libc,use_errno=True)

pthread = find_library("pthread")
if pthread is None:
    raise ImportError("pthreads not found")
pthread = CDLL(pthread,use_errno=True)


SCHED_OTHER = 0
SCHED_FIFO = 1
SCHED_RR = 2


class _sched_param(Structure):
    _fields_ = [("priority",c_int32)]


def _priority_range(policy=None):
    if policy is None:
        policy = libc.sched_getscheduler(0)
        if policy < 0:
            raise OSError(libc.errno,"sched_getscheduler")
    max = libc.sched_get_priority_max(policy)
    if max < 0:
        raise OSError(libc.errno,"sched_get_priority_max")
    min = libc.sched_get_priority_min(policy)
    if min < 0:
        raise OSError(libc.errno,"sched_get_priority_min")
    return (min,max)
    

class Thread(Thread):

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self,priority):
        assert 0 <= priority <= 1
        self.__priority = priority
        if self.is_alive():
            (max,min) = _priority_range()
            range = max - min
            if range <= 0:
                #  We're in a priority-less scheduler, try to change.
                (max,min) = _priority_range(SCHED_RR)
                value = int((max - min) * priority + min)
                value = byref(_sched_param(value))
                res = pthread.pthread_setschedparam(self.ident,SCHED_RR,value)
                if res == errno.EPERM:
                    res = 0
                elif res:
                    raise OSError(res,"pthread_setschedparam")
            else:
                value = int(range * priority + min)
                res = pthread.pthread_setpriority(self.ident,value)
                if res:
                    raise OSError(res,"pthread_setpriority")


