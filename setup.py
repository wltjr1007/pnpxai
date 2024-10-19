r""" \
Open XAI Plug&Play system
=====

Utilities
---------
__version__
    Open XAI PnP version string

__author__
    Author of Open XAI PnP

__homepage__
    Web URL of the documentation

"""
# pylint:disable=broad-except

import os
import subprocess
from configparser import ConfigParser
from distutils.command.build_ext import build_ext
from setuptools import setup, find_packages
import sys
import platform

MAJOR = 0
MINOR = 0
MICRO = 1
ISRELEASED = False
VERSION = f"{MAJOR}.{MINOR}.{MICRO}"

RUN_CYTHON_BUILD = False

min_version = (3, 8, 0)


def is_right_py_version(min_py_version):
    if sys.version_info < (3,):
        sys.stderr.write(
            "Python 2 has reached end-of-life and is no longer supported by Open XAI PnP.")
        return False

    if sys.version_info < min_py_version:
        python_min_version_str = ".".join((str(num) for num in min_py_version))
        no_go = f"You are using Python {platform.python_version()}. Python >={python_min_version_str} is  required."
        sys.stderr.write(no_go)
        return False

    return True


if not is_right_py_version(min_version):
    sys.exit(-1)


# from setuptools import Extension

# Git version stuff
sha = "Unknown"
here = os.path.dirname(os.path.abspath(__file__))

try:
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=here).decode("ascii").strip()
except Exception:
    pass


# Configurations

# All settings are in configs.ini
config = ConfigParser(delimiters=["="])
config.read("configs.ini")
cfg = config["metadata"]

cfg_keys = "description keywords author author_email".split()
expected = cfg_keys + \
    "name user git_branch license status audience language dev_language".split()
for i in expected:
    assert i in cfg, f"Missing expected setting: {i}"

# def set_builtin(name, value):
#     if isinstance(__builtins__, dict):
#         __builtins__[name] = value
#     else:
#         setattr(__builtins__, name, value)

# # Prevent numpy from thinking it is still in its setup process:
# set_builtin("__NUMPY_SETUP__", False)
# import numpy as np


# Defining Setup Variables

NAME = cfg["name"]
AUTHOR = cfg["author"]
AUTHOR_EMAIL = cfg["author_email"]
AUTHOR_LONG = AUTHOR + " <" + AUTHOR_EMAIL + ">"
LICENSE = cfg["license"]
GIT_VERSION = repr(sha)
PLATFORMS = ["Any"]
GIT_URL = cfg["git_url"]
DOCS_URL = cfg["docs_url"]
DOWNLOAD_URL = cfg["download_url"]
PACKAGES = [i for i in find_packages() if "tests" not in i]
DESCRIPTION = cfg["description"]
LONG_DESCRIPTION = open("README.md", encoding="utf-8").read()
KEYWORDS = [i for i in cfg["keywords"].split(", ")]
REQUIREMENTS_FILE = cfg["requirements_file"]
PYTHON_REQUIRES = ">=" + cfg["min_python"]

STATUSES = [
    "1 - Planning",
    "2 - Pre-Alpha",
    "3 - Alpha",
    "4 - Beta",
    "5 - Production/Stable",
    "6 - Mature",
    "7 - Inactive"
]


META_PY_TEXT =\
    """
# This file is automatically generated during the generation of setup.py
# Copyright 2023-2026, Open XAI PnP
author = "%(author)s"
author_email = "%(author_email)s"
version = "%(version)s"
full_version = "%(full_version)s"
git_version = %(git_version)s
release = %(isrelease)s
homepage = "%(homepage)s"
"""


def write_meta(filename="pnpxai/_meta.py"):
    print("[INFO] Writing _meta.py")
    TEXT = META_PY_TEXT
    FULL_VERSION = VERSION
    HOMEPAGE = GIT_URL

    a = open(filename, "w")

    try:
        a.write(TEXT % {"author": AUTHOR,
                        "author_email": str(AUTHOR_EMAIL),
                        "version": VERSION,
                        "full_version": FULL_VERSION,
                        "git_version": GIT_VERSION,
                        "isrelease": str(ISRELEASED),
                        "homepage": str(HOMEPAGE)})
    finally:
        a.close()


def get_docs_url():
    return DOCS_URL


def get_requirements(filename="tools/requirements.txt"):
    requirements = []
    with open(filename) as file:
        for line in file:
            requirements.append(line)
    return requirements


CYTHON_SOURCES = ("",)


def generate_cython():
    cwd = os.path.abspath(os.path.dirname(__file__))
    print("[INFO] Cythonizing sources")
    p = subprocess.call([sys.executable,
                        os.path.join(cwd, "tools", "cythonize.py")],
                        cwd=cwd)
    if p != 0:
        raise RuntimeError("[ERROR] Running cythonize failed!")


copt = {
    "msvc": ["/EHsc"],
    "intelw": ["/EHsc"]
}


class build_extension_class(build_ext):
    def build_extensions(self):
        c = self.compiler.compiler_type
        if c in copt:
            for e in self.extensions:
                e.extra_compile_args = copt[c]
        build_ext.build_extensions(self)


CMDCLASS = {
    "build_ext": build_extension_class
}


def setup_package():
    # Rewrite the meta file everytime
    write_meta()

    metadata = dict(
        name=NAME,
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=AUTHOR,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        url=GIT_URL,
        download_url=DOWNLOAD_URL,
        project_urls={
            "Bug Tracker": GIT_URL + "/issues",
            "Documentation": get_docs_url(),
            "Source Code": GIT_URL,
        },
        packages=PACKAGES,
        # ext_modules = EXT_MODULES,
        license=LICENSE,
        platforms=PLATFORMS,
        install_requires=get_requirements(REQUIREMENTS_FILE),
        python_requires=PYTHON_REQUIRES,
        # cmdclass = CMDCLASS,
        # Include_package_data is required for setup.py to recognize the MAINFEST.in file
        # https://python-packaging.readthedocs.io/en/latest/non-code-files.html
        include_package_data=True,
        zip_safe=False,
        keywords=KEYWORDS,
    )

    # run_build = RUN_CYTHON_BUILD
    # if run_build:
    #     generate_cython()

    setup(**metadata)


if __name__ == "__main__":
    # Running the build is as simple as:
    # >> python setup.py sdist bdist_wheel
    # This command includes building the required Python extensions (Cython included)

    # It"s recommended, however, to use:
    # >> python setup.py build_ext
    # first, and then
    # >> python setup.py sdist bdist_wheel
    setup_package()