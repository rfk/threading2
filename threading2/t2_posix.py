
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


# _cpuset is the structure representing a set of cpus.  Ordinarily you'd
# manipulate it using platform-specific macros, but we don't have that luxury.
# Instread, we adjust the definition of the structure in response to EINVAL.
# TODO: there's no guarantee the cpu_set_t structure is a long array bitmask.
_CPUSET_SIZE = 1
_MAX_CPUSET_SIZE = 8
_HAVE_ADJUSTED_CPUSET_SIZE = False
_cpuset_bits_t = c_int32
class _cpuset(Structure):
    _fields_ = [("bits",_cpuset_bits_t*_CPUSET_SIZE)]

def _incr_cpuset_size():
    global _cpuset
    global _CPUSET_SIZE
    _CPUSET_SIZE += 1
    class _cpuset(Structure):
        _fields_ = [("bits",_cpuset_bits_t*_CPUSET_SIZE)]



def _priority_range(policy=None):
    if policy is None:
        policy = libc.sched_getscheduler(0)
        if policy < 0:
            raise OSError(get_errno(),"sched_getscheduler")
    max = libc.sched_get_priority_max(policy)
    if max < 0:
        raise OSError(get_errno(),"sched_get_priority_max")
    min = libc.sched_get_priority_min(policy)
    if min < 0:
        raise OSError(get_errno(),"sched_get_priority_min")
    return (min,max)
    

if hasattr(libc,"sched_setaffinity"):
    def _do_set_affinity(tid,affinity):
        if not _HAVE_ADJUSTED_CPUSET_SIZE:
            _do_get_affinity(tid)
        affinity = CPUSet(affinity)
        mask = _cpuset()
        bitmask = affinity.to_bitmask()
        chunkmask = 2**(8*sizeof(_cpuset_bits_t))-1
        for i in xrange(_CPUSET_SIZE):
            mask.bits[i] = bitmask & chunkmask
            bitmask = bitmask >> (8*sizeof(_cpuset_bits_t))
        if libc.sched_setaffinity(tid,sizeof(mask),byref(mask)) < 0:
            raise OSError(get_errno(),"sched_setaffinity")
    def _do_get_affinity(tid):
        global _HAVE_ADJUSTED_CPUSET_SIZE
        _HAVE_ADJUSTED_CPUSET_SIZE = True
        mask = _cpuset()
        if libc.sched_getaffinity(tid,sizeof(mask),byref(mask)) < 0:
            eno = get_errno()
            if eno == errno.EINVAL and _CPUSET_SIZE < _MAX_CPUSET_SIZE:
                _incr_cpuset_size()
                return _do_get_affinity(tid)
            raise OSError(eno,"sched_getaffinity")
        intmask = 0
        shift = 8*sizeof(_cpuset_bits_t)
        for i in xrange(len(mask.bits)):
            intmask |= mask.bits[i] << (i*shift)
        return CPUSet(intmask)
elif hasattr(pthread,"pthread_setaffinity_np"):
    def _do_set_affinity(tid,affinity):
        if not _HAVE_ADJUSTED_CPUSET_SIZE:
            _do_get_affinity(tid)
        affinity = CPUSet(affinity)
        mask = c_long()
        mask.value = affinity.to_bitmask()
        res = pthread.pthread_setaffinity_np(tid,sizeof(mask),byref(mask))
        if res:
            raise OSError(res,"pthread_setaffinity_np")
    def _do_get_affinity(tid):
        global _HAVE_ADJUSTED_CPUSET_SIZE
        _HAVE_ADJUSTED_CPUSET_SIZE = True
        mask = _cpuset()
        res = pthread.pthread_getaffinity_np(tid,sizeof(mask),byref(mask))
        if res:
            if res == errno.EINVAL and _CPUSET_SIZE < _MAX_CPUSET_SIZE:
                _incr_cpuset_size()
                return _do_get_affinity(tid)
            raise OSError(res,"pthread_get_affinity_no")
        intmask = 0
        shift = 8*sizeof(_cpuset_bits_t)
        for i in xrange(len(mask.bits)):
            intmask |= mask.bits[i] << (i*shift)
        return CPUSet(intmask)
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


