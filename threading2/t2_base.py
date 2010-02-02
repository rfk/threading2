
import threading2
from threading import *
from threading import _RLock,_Event,_Condition,_Semaphore,_BoundedSemaphore, \
                      _Timer,ThreadError,_time,_sleep,_get_ident


__all__ = ["active_count","activeCount","Condition","current_thread",
           "currentThread","enumerate","Event","local","Lock","RLock",
           "Semaphore","BoundedSemaphore","Thread","Timer","setprofile",
           "settrace","stack_size"]
           


#  Expose the actual class objects, rather than the strange function-based
#  wrappers that threading wants to stick you with.
RLock = _RLock
Event = _Event
Condition = _Condition
Semaphore = _Semaphore
BoundedSemaphore = _BoundedSemaphore
Timer = _Timer


class Thread(Thread):
    """Extended Thread class.

    This is a subclass of the standard python Thread, which adds support
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

    def __init__(self,group=None,target=None,name=None,args=(),kwargs={},
                 daemon=None,priority=None,affinity=None):
        super(Thread,self).__init__(None,target,name,args,kwargs)
        self.__ident = None
        if daemon is not None:
            self.daemon = daemon
        if group is None:
            self.group = threading2.default_group
        else:
            self.group = group
        if priority is not None:
            self._set_priority(priority)
        else:
            self.__priority = None
        if affinity is not None:
            self._set_affinity(affinity)
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
        for new_cls in self.__mro__:
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
                new_cls._update_thread(thread)
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
    priority = property(_get_priority,_set_priority)

    def _get_affinity(self):
        return self.__affinity
    def _set_affinity(self,affinity):
        self.__affinity = affinity
    affinity = property(_get_affinity,_set_affinity)


