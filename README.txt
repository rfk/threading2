

  threading2:  like the standard threading module, but awesomer.

This module is designed as a drop-in replacement and extension for the default
"threading" module.  It has two main objectives:

    * implement primitives using native platform functionality where possible
    * expose more sophisticated functionality where it can be done uniformly

The following extensions are currently implemented:

    * ability to set (advisory) thread priority
    * ability to set (advisory) CPU affinity at thread and process level
    * thread groups for simultaneous management of multiple threads
    * SHLock class for shared/exclusive (also known as read/write) locks

The following API niceties are also included:

    * all blocking methods take a "timeout" argument and return a success code
    * all exposed objects are actual classes and can be safely subclassed

This has currently only been tested on WinXP and Ubuntu Karmic; similar 
platforms *should* work OK, and other platforms *should* fall back to using
sensible default behaviour, but I'm not making any guarantees at this stage.

Additional planned extensions include:

    * make stack_size a kwarg when creating a thread
    * native events, semaphores and timed waits on win32
    * native conditions and timed waits on pthreads platforms
    * native SHLock implementations (SRW on Win Vista+, pthread_rwlock)

