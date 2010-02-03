

  threading2:  like the threading module, but awesomer.

This module is designed as a drop-in replacement and extension for the default
"threading" module.  It has two main objectives:

    * implement primitives using native threading functions where possible
    * expose more sophisticated functionality where if can be done uniformly

Some highlights (will eventually) include:

    * ability to set (advisory) thread priorities and affinities
    * all blocking calls take "timeout" keyword parameter
    * native events and semaphores on win32 and pthreads platforms
    * all exposed objects are actual classes and can be safely subclassed
    * thread groups for simultaneous management of multiple threads

