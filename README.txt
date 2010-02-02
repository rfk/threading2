

  withrestart:  structured error recovery using named restart functions

This is a Pythonisation (Lispers might rightly say "bastardisation") of the
restart-based condition system of Common Lisp.  It's designed to make error
recovery simpler and easier by removing the assumption that unhandled errors
must be fatal.

A "restart" represents a named strategy for resuming execution of a function
after the occurrence of an error.  At any point during its execution a
function can push a Restart object onto its call stack.  If an exception
occurs within the scope of that Restart, code higher-up in the call chain can
invoke it to recover from the error and let the function continue execution.
By providing several restarts, functions can offer several different strategies
for recovering from errors.

A "handler" represents a higher-level strategy for dealing with the occurrence
of an error.  It is conceptually similar to an "except" clause, in that one
establishes a suite of Handler objects to be invoked if an error occurs during
the execution of some code.  There is, however, a crucial difference: handlers
are executed without unwinding the call stack.  They thus have the opportunity
to take corrective action and then resume execution of whatever function
raised the error.

For example, consider a function that reads the contents of all files from a 
directory into a dict in memory::

   def readall(dirname):
       data = {}
       for filename in os.listdir(dirname):
           filepath = os.path.join(dirname,filename)
           data[filename] = open(filepath).read()
       return data

If one of the files goes missing after the call to os.listdir() then the
subsequent open() will raise an IOError.  While we could catch and handle the
error inside this function, what would be the appropriate action?  Should
files that go missing be silently ignored?  Should they be re-created with
some default contents?  Should a special sentinel value be placed in the
data dictionary?  What value?  The readall() function does not have enough
information to decide on an appropriate recovery strategy.

Instead, readall() can provide the *infrastructure* for doing error recovery
and leave the final decision up to the calling code.  The following definition
uses three pre-defined restarts to let the calling code (a) skip the missing
file completely, (2) retry the call to open() after taking some corrective
action, or (3) use some other value in place of the missing file::

   def readall(dirname):
       data = {}
       for filename in os.listdir(dirname):
           filepath = os.path.join(dirname,filename)
           with restarts(skip,retry,use_value) as invoke:
               data[filename] = invoke(open,filepath).read()
       return data

Of note here is the use of the "with" statement to establish a new context
in the scope of restarts, and use of the "invoke" wrapper when calling a
function that might fail.  The latter allows restarts to inject an alternate
return value for the failed function.

Here's how the calling code would look if it wanted to silently skip the
missing file::

   def concatenate(dirname):
       with Handler(IOError,"skip"):
           data = readall(dirname)
       return "".join(data.itervalues())

This pushes a Handler instance into the execution context, which will detect
IOError instances and respond by invoking the "skip" restart point.  If this
handler is invoked in response to an IOError, execution of the readall()
function will continue immediately following the "with restarts(...)" block.

Note that there is no way to achieve this skip-and-continue behaviour using an
ordinary try-except block; by the time the IOError has propagated up to the
concatenate() function for processing, all context from the execution of 
readall() will have been unwound and cannot be resumed.

Calling code that wanted to re-create the missing file would simply push a
different error handler::

   def concatenate(dirname):
       def handle_IOError(e):
           open(e.filename,"w").write("MISSING")
           raise InvokeRestart("retry")
       with Handler(IOError,handle_IOError):
           data = readall(dirname)
       return "".join(data.itervalues())

By raising InvokeRestart, this handler transfers control back to the restart
that was  established by the readall() function.  This particular restart
will re-execute the failing function call and let readall() continue with its
operation.

Calling code that wanted to use a special sentinel value would use a handler
to pass the required value to the "use_value" restart::

   def concatenate(dirname):
       class MissingFile:
           def read():
               return "MISSING"
       def handle_IOError(e):
           raise InvokeRestart("use_value",MissingFile())
       with Handler(IOError,handle_IOError):
           data = readall(dirname)
       return "".join(data.itervalues())


By separating the low-level details of recovering from an error from the
high-level strategy of what action to take, it's possible to create quite
powerful recovery mechanisms.

While this module provides a handful of pre-built restarts, functions will
usually want to create their own.  This can be done by passing a callback
into the Restart object constructor::

   def readall(dirname):
       data = {}
       for filename in os.listdir(dirname):
           filepath = os.path.join(dirname,filename)
           def log_error():
               print "an error occurred"
           with Restart(log_error):
               data[filename] = open(filepath).read()
       return data


Or by using a decorator to define restarts inline::

   def readall(dirname):
       data = {}
       for filename in os.listdir(dirname):
           filepath = os.path.join(dirname,filename)
           with restarts() as invoke:
               @invoke.add_restart
               def log_error():
                   print "an error occurred"
               data[filename] = open(filepath).read()
       return data

Handlers can also be defined inline using a similar syntax::

   def concatenate(dirname):
       with handlers() as h:
           @h.add_handler
           def IOError(e):
               open(e.filename,"w").write("MISSING")
               raise InvokeRestart("retry")
           data = readall(dirname)
       return "".join(data.itervalues())


Now finally, a disclaimer.  I've never written any Common Lisp.  I've only read
about the Common Lisp condition system and how awesome it is.  I'm sure there
are many things that it can do that this module simply cannot.  For example:

  * Since this is built on top of a standard exception-throwing system, the
    handlers can only be executed after the stack has been unwound to the
    most recent restart context; in Common Lisp they're executed without
    unwinding the stack at all.
  * Since this is built on top of a standard exception-throwing system, it's
    probably too heavyweight to use for generic condition signalling system.

Nevertheless, there's no shame in pinching a good idea when you see one...

