
from distutils.core import setup

import threading2
VERSION = threading2.__version__

NAME = "threading2"
DESCRIPTION = "like the standard threading module, but awesomer"
LONG_DESC = threading2.__doc__
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = "http://github.com/rfk/threading2"
LICENSE = "MIT"
KEYWORDS = "thread threading"

setup(name=NAME,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=LONG_DESC,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=["threading2","threading2.tests","threading2.tests.stdregr"],
     )

