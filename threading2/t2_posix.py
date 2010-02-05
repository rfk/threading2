
import os
import errno
from ctypes import *
from ctypes.util import find_library

import t2_base
from t2_base import *
from t2_base import __all__

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
    

# TODO: there's no guarantee that the cpu_set_t structure is a long bitmask.
# TODO: this will only work up to 32 cpus.  should use system_affinity() to
#       find max cpu number, then send in an appropriately-sized array of
#       longs rather than a single long.
if hasattr(libc,"sched_setaffinity"):
    def _do_set_affinity(tid,affinity):
        affinity = CPUSet(affinity)
        mask = c_long()
        mask.value = affinity.to_bitmask()
        if libc.sched_setaffinity(tid,sizeof(mask),byref(mask)) < 0:
            raise OSError(libc.errno,"sched_setaffinity")
    def _do_get_affinity(tid):
        mask = c_long()
        if libc.sched_getaffinity(tid,sizeof(mask),byref(mask)) < 0:
            raise OSError(libc.errno,"sched_getaffinity")
        return CPUSet(mask.value)
elif hasattr(pthread,"pthread_setaffinity_np"):
    def _do_set_affinity(tid,affinity):
        affinity = CPUSet(affinity)
        mask = c_long()
        mask.value = affinity.to_bitmask()
        res = pthread.pthread_setaffinity_np(tid,sizeof(mask),byref(mask))
        if res:
            raise OSError(res,"pthread_setaffinity_np")
    def _do_get_affinity(tid):
        mask = c_long()
        res = pthread.pthread_getaffinity_np(tid,sizeof(mask),byref(mask))
        if res:
            raise OSError(res,"pthread_getaffinity_np")
        return CPUSet(mask.value)
else:
    _do_set_affinity = None
    _do_get_affinity = None



class Thread(Thread):

    if hasattr(pthread,"pthread_setpriority"):
        def _set_priority(self,priority):
            priority = super(Thread,self)._set_priority(priority)
            me = self.ident
            (max,min) = _priority_range()
            range = max - min
            if range <= 0:
                if hasattr(pthread,"pthread_setschedparam"):
                    #  We're in a priority-less scheduler, try to change.
                    (max,min) = _priority_range(SCHED_RR)
                    value = int((max - min) * priority + min)
                    value = byref(_sched_param(value))
                    res = pthread.pthread_setschedparam(me,SCHED_RR,value)
                    if res == errno.EPERM:
                        res = 0
                    elif res:
                        raise OSError(res,"pthread_setschedparam")
            else:
                value = int(range * priority + min)
                if pthread.pthread_setpriority(me,value):
                    raise OSError(res,"pthread_setpriority")
            return priority

    if _do_set_affinity is not None:
        def _set_affinity(self,affinity):
            affinity = super(Thread,self)._set_affinity(affinity)
            me = self.ident
            _do_set_affinity(me,affinity)
            return affinity


def system_affinity():
    #  Try to read cpu info from /proc
    try:
        with open("/proc/cpuinfo","r") as cpuinfo:
            affinity = CPUSet()
            for ln in cpuinfo:
                info = ln.split()
                if len(info) == 3:
                    if info[0] == "processor" and info[1] == ":":
                         affinity.add(info[2])
            return affinity
    except EnvironmentError:
        pass
    #  Fall back to the process affinity
    return process_affinity()
system_affinity.__doc__ = t2_base.system_affinity.__doc__


if _do_set_affinity is not None:
    def process_affinity(affinity=None):
        pid = os.getpid()
        if affinity is not None:
            _do_set_affinity(pid,affinity)
        return _do_get_affinity(pid)
    process_affinity.__doc__ = t2_base.process_affinity.__doc__


