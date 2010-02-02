
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

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self,priority):
        assert 0 <= priority <= 1
        self.__priority = priority
        if self.is_alive():
            if priority == 1:
                # max == THREAD_PRIORITY_TIME_CRITICAL
                value = 15
            elif priority == 0:
                # min == THREAD_PRIORITY_IDLE
                value = -15
            else:
                # Spread the rest evenly over the five levels from -2 to 2
                # (THREAD_PRIORITY_LOWEST through THREAD_PRIORITY_HIGHEST)
                value = int(round(4*priority) - 2)
            handle = kernel32.OpenThread(THREAD_SET_INFORMATION,False,self.__w32id)
            try:
                res = kernel32.SetThreadPriority(handle,value)
                if not res:
                    raise WinError()
            finally:
                kernel32.CloseHandle(handle)

