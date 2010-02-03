
from __future__ import with_statement

import os
import sys
import unittest
import doctest

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

