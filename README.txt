

  threading2:  like the standard threading module, but awesomer.

This module is designed as a drop-in replacement and extension for the default
"threading" module.  It has two main objectives:

    * implement primitives using native platform functionality where possible
    * expose more sophisticated functionality where it can be done uniformly

The following extensions are currently implemented:

    * ability to set (advisory) thread priority
    * thread groups for simultaneous management of multiple threads

The following API niceties are also included:

    * all blocking methods take a "timeout" argument and return a success code
    * all exposed objects are actual classes and can be safely subclassed

Planned extensions include:

    * ability to set (advisory) thread affinities
    * native events, semaphores and timed waits on win32
    * native conditions and timed waits on pthreads platforms

Stuff that might get included one day:

    * ReadWriteLock (with SRW on Win Vista+, pthread_rwlock on posix)

