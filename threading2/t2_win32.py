
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


def _GetProcessAffinityMask():
    pmask = c_int()
    smask = c_int()
    p = kernel32.GetCurrentProcess()
    if not kernel32.GetProcessAffinityMask(p,byref(pmask),byref(smask)):
        raise WinError()
    return (pmask.value,smask.value)


class CPUAffinity(CPUAffinity):

    if hasattr(kernel32,"GetProcessAffinityMask"):

        _system_affinity = CPUAffinity(_GetProcessAffinityMask()[1])

        @classmethod
        def get_system_affinity(cls):
            """Get the CPU affinity mask for the current process."""
            return cls._system_affinity

        @classmethod
        def get_process_affinity(cls):
            """Get the CPU affinity mask for the current process."""
            return CPUAffinity(_GetProcessAffinityMask()[0])

        @classmethod
        def set_process_affinity(cls,affinity):
            """Get the CPU affinity mask for the current process."""
            affinity = cls(affinity)
            mask = affinity.to_bitmask()
            p = kernel32.GetCurrentProcess()
            if not kernel32.SetProcessorAffinityMask(p,mask):
                raise WinError()


