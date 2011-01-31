
import t2_base
from t2_base import *
from t2_base import __all__

import errno
from ctypes import *

kernel32 = windll.kernel32

THREAD_SET_INFORMATION = 0x20
THREAD_PRIORITY_ABOVE_NORMAL = 1


class Thread(Thread):

    def before_run(self):
        self.__w32id = kernel32.GetCurrentThreadId()
        super(Thread,self).before_run()

    if hasattr(kernel32,"SetThreadPriority"):
        def _set_priority(self,priority):
            priority = super(Thread,self)._set_priority(priority)
            if priority >= 0.95:
                # max == THREAD_PRIORITY_TIME_CRITICAL
                value = 15
            elif priority <= 0.05:
                # min == THREAD_PRIORITY_IDLE
                value = -15
            else:
                # Spread the rest evenly over the five levels from -2 to 2
                # (THREAD_PRIORITY_LOWEST through THREAD_PRIORITY_HIGHEST)
                value = int(round(4*priority) - 2)
            handle = kernel32.OpenThread(THREAD_SET_INFORMATION,False,self.__w32id)
            value = c_int(value)
            try:
                if not kernel32.SetThreadPriority(handle,value):
                    raise WinError()
            finally:
                kernel32.CloseHandle(handle)
            return priority


    if hasattr(kernel32,"SetThreadAffinityMask"):
        def _set_affinity(self,affinity):
            affinity = super(Thread,self)._set_affinity(affinity)
            mask = affinity.to_bitmask()
            handle = kernel32.OpenThread(THREAD_SET_INFORMATION,False,self.__w32id)
            try:
                if not kernel32.SetThreadAffinityMask(handle,mask):
                    raise WinError()
            finally:
                kernel32.CloseHandle(handle)
            return affinity



if hasattr(kernel32,"GetProcessAffinityMask"):

    def _GetProcessAffinityMask():
        pmask = c_int()
        smask = c_int()
        p = kernel32.GetCurrentProcess()
        if not kernel32.GetProcessAffinityMask(p,byref(pmask),byref(smask)):
            raise WinError()
        return (pmask.value,smask.value)

    def system_affinity():
       return CPUSet(_GetProcessAffinityMask()[1])
    system_affinity.__doc__ = t2_base.system_affinity.__doc__

    def process_affinity(affinity=None):
        if affinity is not None:
            mask = CPUSet(affinity).to_bitmask()
            p = kernel32.GetCurrentProcess()
            if not kernel32.SetProcessAffinityMask(p,mask):
                raise WinError()
        return CPUSet(_GetProcessAffinityMask()[0])
    process_affinity.__doc__ = t2_base.process_affinity.__doc__


