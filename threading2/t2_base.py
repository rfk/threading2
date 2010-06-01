
import threading2
from threading import *
from threading import _RLock,_Event,_Condition,_Semaphore,_BoundedSemaphore, \
                      _Timer,ThreadError,_time,_sleep,_get_ident,_allocate_lock


__all__ = ["active_count","activeCount","Condition","current_thread",
           "currentThread","enumerate","Event","local","Lock","RLock",
           "Semaphore","BoundedSemaphore","Thread","Timer","setprofile",
           "settrace","stack_size","CPUSet","system_affinity",
           "process_affinity"]
           


class _ContextManagerMixin(object):
    """Simple mixin mapping __enter__/__exit__ to acquire/release."""

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        self.release()


class Lock(_ContextManagerMixin):
    """Class-based Lock object.

    This is a very thin wrapper around Python's native lock objects.  It's
    here to provide easy subclassability and to add a "timeout" argument
    to Lock.acquire().
    """

    def __init__(self):
        self.__lock = _allocate_lock()
        super(Lock,self).__init__()

    def acquire(self,blocking=True,timeout=None):
        """Attempt to acquire this lock.

        If the optional argument "blocking" is True and "timeout" is None,
        this methods blocks until is successfully acquires the lock.  If
        "blocking" is False, it returns immediately if the lock could not
        be acquired.  Otherwise, it blocks for at most "timeout" seconds
        trying to acquire the lock.

        In all cases, this methods returns True if the lock was successfully
        acquired and False otherwise.
        """
        if timeout is None:
            return self.__lock.acquire(blocking)
        else:
            #  Simulated timeout using progressively longer sleeps.
            #  This is the same timeout scheme used in the stdlib Condition
            #  class.  If there's lots of contention on the lock then there's
            #  a good chance you won't get it; but then again, Python doesn't
            #  guarantee fairness anyway.  We hope that platform-specific
            #  extensions can provide a better mechanism.
            endtime = _time() + timeout
            delay = 0.0005
            while not self.__lock.acquire(False):
                remaining = endtime - _time()
                if remaining <= 0:
                    return False
                delay = min(delay*2,remaining,0.05)
                _sleep(delay)
            return True
             
    def release(self):
        """Release this lock."""
        self.__lock.release()


class RLock(_ContextManagerMixin,_RLock):
    """Re-implemented RLock object.

    This is pretty much a direct clone of the RLock object from the standard
    threading module; the only difference is that it uses a custom Lock class
    so that acquire() has a "timeout" parameter.

    It also includes a fix for a memory leak present in Python 2.6 and older.
    """

    _LockClass = Lock

    def __init__(self):
        super(RLock,self).__init__()
        self.__block = self._LockClass()
        self.__owner = None
        self.__count = 0

    def acquire(self,blocking=True,timeout=None):
        me = _get_ident()
        if self.__owner == me:
            self.__count += 1
            return True
        if self.__block.acquire(blocking,timeout):
            self.__owner = me
            self.__count = 1
            return True
        return False

    def release(self):
        if self.__owner != _get_ident():
            raise RuntimeError("cannot release un-aquired lock")
        self.__count -= 1
        if not self.__count:
            self.__owner = None
            self.__block.release()

    def _is_owned(self):
        return self.__owner == _get_ident()



class Condition(_Condition):
    """Re-implemented Condition class.

    This is pretty much a direct clone of the Condition class from the standard
    threading module; the only difference is that it uses a custom Lock class
    so that acquire() has a "timeout" parameter.
    """

    _LockClass = RLock
    _WaiterLockClass = Lock

    def __init__(self,lock=None):
        if lock is None:
            lock = self._LockClass()
        super(Condition,self).__init__(lock)

    #  This is essentially the same as the base version, but it returns
    #  True if the wait was successful and False if it timed out.
    def wait(self,timeout=None):
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-aquired lock")
        waiter = self._WaiterLockClass()
        waiter.acquire()
        self.__waiters.append(waiter)
        saved_state = self._release_save()
        try:
            if not waiter.acquire(timeout=timeout):
                try:
                    self.__waiters.remove(waiter)
                except ValueError:
                    pass
                return False
            else:
                return True
        finally:
            self._acquire_restore(saved_state)


class Semaphore(_ContextManagerMixin):
    """Re-implemented Semaphore class.

    This is pretty much a direct clone of the Semaphore class from the standard
    threading module; the only difference is that it uses a custom Condition
    class so that acquire() has a "timeout" parameter.
    """

    _ConditionClass = Condition

    def __init__(self,value=1):
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        super(Semaphore,self).__init__()
        self.__cond = self._ConditionClass()
        self.__value = value

    def acquire(self,blocking=True,timeout=None):
        with self.__cond:
            while self.__value == 0:
                if not blocking:
                    return False
                if not self.__cond.wait(timeout=timeout):
                    return False
            self.__value = self.__value - 1
            return True

    def release(self):
        with self.__cond:
            self.__value = self.__value + 1
            self.__cond.notify()


class BoundedSemaphore(Semaphore):
    """Semaphore that checks that # releases is <= # acquires"""

    def __init__(self,value=1):
        super(BoundedSemaphore,self).__init__(value)
        self._initial_value = value

    def release(self):
        if self._Semaphore__value >= self._initial_value:
            raise ValueError("Semaphore released too many times")
        return super(BoundedSemaphore,self).release()


class Event(object):
    """Re-implemented Event class.

    This is pretty much a direct clone of the Event class from the standard
    threading module; the only difference is that it uses a custom Condition
    class for easy extensibility.
    """

    _ConditionClass = Condition

    def __init__(self):
        super(Event,self).__init__()
        self.__cond = self._ConditionClass()
        self.__flag = False

    def is_set(self):
        return self.__flag
    isSet = is_set

    def set(self):
        with self.__cond:
            self.__flag = True
            self.__cond.notify_all()

    def clear(self):
        with self.__cond:
            self.__flag = False

    def wait(self,timeout=None):
        with self.__cond:
            if self.__flag:
                return True
            return self.__cond.wait(timeout)


class Timer(_Timer):
    """Re-implemented Timer class.

    Actually there's nothing new here, it just exposes the Timer class from
    the stdlib as a normal class in case you want to extend it.
    """
    pass


class Thread(Thread):
    """Extended Thread class.

    This is a subclass of the standard python Thread class, which adds support
    for the following new features:

        * a "priority" attribute, through which you can set the (advisory)
          priority of a thread to a float between 0 and 1.
        * an "affinity" attribute, through which you can set the (advisory)
          CPU affinity of a thread.
        * before_run() and after_run() methods that can be safely extended
          in subclasses.

    It also provides some niceities over the standard thread class:

        * support for thread groups using the existing "group" argument
        * support for "daemon" as an argument to the constructor
        * join() returns a bool indicating success of the join

    """

    _ConditionClass = None

    def __init__(self,group=None,target=None,name=None,args=(),kwargs={},
                 daemon=None,priority=None,affinity=None):
        super(Thread,self).__init__(None,target,name,args,kwargs)
        if self._ConditionClass is not None:
            self.__block = self._ConditionClass()
        self.__ident = None
        if daemon is not None:
            self.daemon = daemon
        if group is None:
            self.group = threading2.default_group
        else:
            self.group = group
        if priority is not None:
            self.priority = priority
        else:
            self.__priority = None
        if affinity is not None:
            self.affinity = affinity
        else:
            self.__affinity = None
       
    @classmethod
    def from_thread(cls,thread):
        """Convert a vanilla thread object into an instance of this class.

        This method "upgrades" a vanilla thread object to an instance of this
        extended class.  You might need to call this if you obtain a reference
        to a thread by some means other than (a) creating it, or (b) from the 
        methods of the threading2 module.
        """
        new_classes = []
        for new_cls in cls.__mro__:
            if new_cls not in thread.__class__.__mro__:
                new_classes.append(new_cls)
        if isinstance(thread,cls):
            pass
        elif issubclass(cls,thread.__class__):
            thread.__class__ = cls
        else:
            class UpgradedThread(thread.__class__,cls):
                pass
            thread.__class__ = UpgradedThread
        for new_cls in new_classes:
            if hasattr(new_cls,"_upgrade_thread"):
                new_cls._upgrade_thread(thread)
        return thread

    def _upgrade_thread(self):
        self.__priority = None
        self.__affinity = None
        if getattr(self,"group",None) is None:
            self.group = threading2.default_group

    def join(self,timeout=None):
        super(Thread,self).join(timeout)
        return not self.is_alive()

    def start(self):
        #  Trick the base class into running our wrapper methods
        self_run = self.run
        def run():
            self.before_run()
            try:
                self_run()
            finally:
                self.after_run()
        self.run = run
        super(Thread,self).start()

    def before_run(self):
        if self.__priority is not None:
            self._set_priority(self.__priority)

    def after_run(self):
        pass

    #  Backport "ident" attribute for older python versions
    if "ident" not in Thread.__dict__:
        def before_run(self):
            self.__ident = _get_ident()
            if self.__priority is not None:
                self._set_priority(self.__priority)
        @property
        def ident(self):
            return self.__ident

    def _get_group(self):
        return self.__group
    def _set_group(self,group):
        try:
            self.__group
        except AttributeError:
            self.__group = group
            group._add_thread(self)
        else:
            raise AttributeError("cannot set group after thread creation")
    group = property(_get_group,_set_group)

    def _get_priority(self):
        return self.__priority
    def _set_priority(self,priority):
        if not 0 <= priority <= 1:
            raise ValueError("priority must be between 0 and 1")
        self.__priority = priority
        if self.is_alive():
            self.priority = priority
        return priority
    priority = property(_get_priority,_set_priority)
    def _set_priority(self,priority):
        return priority

    def _get_affinity(self):
        return self.__affinity
    def _set_affinity(self,affinity):
        if not isinstance(affinity,CPUSet):
            affinity = CPUSet(affinity)
        self.__affinity = affinity
        if self.is_alive():
            self.affinity = affinity
        return affinity
    affinity = property(_get_affinity,_set_affinity)
    def _set_affinity(self,affinity):
        return affinity


#  Utilities for handling CPU affinity

class CPUSet(set):
    """Object representing a set of CPUs on which a thread is to run.

    This is a python-level representation of the concept of a "CPU mask" as
    used in various thread-affinity libraries.  Each CPU in the system is
    represented by an integer, with the first being CPU zero.
    """

    def __init__(self,set_or_mask=None):
        super(CPUSet,self).__init__()
        if set_or_mask is not None:
            if isinstance(set_or_mask,(int,long)):
                cpu = 0
                cur_mask = set_or_mask
                while cur_mask:
                    if cur_mask & 1:
                        self.add(cpu)
                    cur_mask = cur_mask >> 1
                    cpu += 1
            else:
                for i in set_or_mask:
                    self.add(i)

    def add(self,cpu):
        return super(CPUSet,self).add(int(cpu))

    def to_bitmask(self):
        bitmask = 0
        for cpu in self:
            bitmask |= 1 << cpu
        return bitmask


def system_affinity():
    """Get the set of CPUs available on this system."""
    return CPUSet((0,))


def process_affinity(affinity=None):
    """Get or set the CPU affinity set for the current process.

    This will affect all future threads spawned by this process.  It is
    implementation-defined whether it will also affect previously-spawned
    threads.
    """
    if affinity is not None:
        affinity = CPUSet(affinity)
        if affinity != system_affinity():
            raise ValueError("unknown cpus: %s" % affinity)
    return system_affinity()


