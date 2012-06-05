#!/usr/bin/env python2

from distutils.core import setup
import shutil
import os

shutil.copyfile("mint.py", "mint")

setup(
    name="mint",
    version="20120604",
    description="Check the balance of mint.com accounts",
    author="Spencer Judd",
    author_email="spencercjudd@gmail.com",
    url="https://github.com/scjudd/mint",
    scripts=['mint'],
)

try:
    os.remove("mint")
except:
    pass
