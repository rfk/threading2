
from __future__ import with_statement

import os
import sys
import unittest
import doctest
import random
import time

import threading2
from threading2 import *

#  Grab everything needed to run standard threading test function
from threading import _test as std_threading_test
from threading import _Verbose, _sleep
from collections import deque


class TestStandard(unittest.TestCase):
    """Run standard threading testcases using our new classes."""

    def test_standard(self):
        exec std_threading_test.func_code in globals()


class TestSHLock(unittest.TestCase):
    """Testcases for SHLock class."""

    def test_contention(self):
        lock = SHLock()
        done = []
        def lots_of_acquires():
            for _ in xrange(1000):
                shared = random.choice([True,False])
                lock.acquire(shared=shared)
                lock.acquire(shared=shared)
                time.sleep(random.random() * 0.0001)
                lock.release()
                time.sleep(random.random() * 0.0001)
                lock.acquire(shared=shared)
                time.sleep(random.random() * 0.0001)
                lock.release()
                lock.release()
            done.append(True)
        threads = [Thread(target=lots_of_acquires) for _ in xrange(3)]
        for t in threads:
            t.daemon = True
            t.start()
        for t in threads:
            if not t.join(timeout=10):
                raise RuntimeError("SHLock deadlock")
        if len(done) != len(threads):
            print done, threads
            raise RuntimeError("SHLock test error")

class TestSHLockContext(unittest.TestCase):
    class TestPassed(Exception): pass

    @staticmethod
    def raise_test_passed(): raise TestSHLockContext.TestPassed

    @staticmethod
    def noop(*args, **kwargs): pass

    def check_args(self, passed, expected):
        def f(**f_kwargs):
            self.assertItemsEqual(expected.items(), f_kwargs.items(), 'Passed {} Got {} Expected {}'.format(passed, f_kwargs, expected))
            raise TestSHLockContext.TestPassed
        return f

    def test_context_without_args(self):

        lock_acquire = SHLock()
        lock_acquire.acquire = TestSHLockContext.raise_test_passed
        with self.assertRaises(TestSHLockContext.TestPassed):
            with lock_acquire:
                pass

        lock_release = SHLock()
        lock_release.release = TestSHLockContext.raise_test_passed
        with self.assertRaises(TestSHLockContext.TestPassed):
            with lock_release:
                pass

    def test_context_with_args(self):
        for passed,expected in (
                ({}, {'shared':False, 'blocking':True, 'timeout':None}),
                ({'shared':True}, {'shared':True, 'blocking':True, 'timeout':None}),
                ({'blocking':False}, {'shared':False, 'blocking':False, 'timeout':None}),
                ({'timeout':1}, {'shared':False, 'blocking':True, 'timeout':1}),
                ):
            lock_acquire_arg = SHLock()
            lock_acquire_arg.acquire = self.check_args(passed, expected)
            with self.assertRaises(TestSHLockContext.TestPassed):
                with lock_acquire_arg(**passed):
                    pass

            lock_release_arg = SHLock()
            lock_acquire_arg.acquire = TestSHLockContext.noop
            lock_release_arg.release = TestSHLockContext.raise_test_passed
            with self.assertRaises(TestSHLockContext.TestPassed):
                with lock_release_arg(**passed):
                    pass

class TestCPUSet(unittest.TestCase):
    """Unittests for CPUSet class."""

    def test_initialisation(self):
        def assertSetEquals(set1,set2):
            self.assertEquals(sorted(list(set1)),sorted(list(set2)))
        # Initialisation from iterables
        assertSetEquals(CPUSet(),[])
        assertSetEquals(CPUSet([0,3,2]),[0,2,3])
        assertSetEquals(CPUSet(""),[])
        assertSetEquals(CPUSet("3158"),[1,3,5,8])
        assertSetEquals(CPUSet("3158"),[1,3,5,8])
        # Initialisation from bitmasks
        assertSetEquals(CPUSet(0),[])
        assertSetEquals(CPUSet(1),[0])
        assertSetEquals(CPUSet(2),[1])
        assertSetEquals(CPUSet(3),[0,1])
        assertSetEquals(CPUSet(4),[2])
        assertSetEquals(CPUSet(5),[0,2])
        assertSetEquals(CPUSet(6),[1,2])
        assertSetEquals(CPUSet(7),[0,1,2])
        assertSetEquals(CPUSet(1 << 7),[7])
        assertSetEquals(CPUSet(1 << 127),[127])
        assertSetEquals(CPUSet(1 << 128),[128])

    def test_to_bitmask(self):
        self.assertEquals(CPUSet().to_bitmask(),0)
        self.assertEquals(CPUSet("0").to_bitmask(),1)
        self.assertEquals(CPUSet("1").to_bitmask(),2)
        self.assertEquals(CPUSet("01").to_bitmask(),3)
        self.assertEquals(CPUSet("2").to_bitmask(),4)
        self.assertEquals(CPUSet("02").to_bitmask(),5)
        self.assertEquals(CPUSet("12").to_bitmask(),6)
        self.assertEquals(CPUSet("012").to_bitmask(),7)
        for i in xrange(100):
            self.assertEquals(CPUSet(i).to_bitmask(),i)

class TestMisc(unittest.TestCase):
    """Miscellaneous test procedures."""

    def test_docstrings(self):
        """Test threading2 docstrings."""
        assert doctest.testmod(threading2)[0] == 0

    def test_README(self):
        """Ensure that the README is in sync with the docstring.

        This test should always pass; if the README is out of sync it just
        updates it with the contents of threading2.__doc__.
        """
        dirname = os.path.dirname
        readme = os.path.join(dirname(dirname(dirname(__file__))),"README.txt")
        if not os.path.isfile(readme):
            f = open(readme,"wb")
            f.write(threading2.__doc__)
            f.close()
        else:
            f = open(readme,"rb")
            if f.read() != threading2.__doc__:
                f.close()
                f = open(readme,"wb")
                f.write(threading2.__doc__)
                f.close()

