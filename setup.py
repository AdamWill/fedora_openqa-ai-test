import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''
        self.test_suite = 'tests'

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args.split())
        sys.exit(errno)

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below. Stolen from
# https://pythonhosted.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# this is sloppy and wrong, see https://stackoverflow.com/a/4792601
# discussion, but should be okay for our purposes. the problem here
# is that if you run 'python3 setup.py install' with all the install
# requires in place, setuptools installs scripts from several of the
# deps to /usr/local/bin , overriding the system copies in /usr/bin.
# This seems to happen when the copy in /usr/bin is for Python 2 not
# Python 3 - e.g. because /usr/bin/fedmsg-logger is Python 2, if you
# do 'python3 setup.py install' here, due to the fedmsg dep, you get
# a /usr/local/bin/fedmsg-logger which is Python 3...we want to be
# able to avoid this, so hack up a 'no deps'
if "--nodeps" in sys.argv:
    INSTALLREQS = []
    sys.argv.remove("--nodeps")
else:
    INSTALLREQS = open('install.requires').read().splitlines()

setup(
    name="fedora_openqa",
    version="3.0.0",
    entry_points={
        'console_scripts': [
            'fedora-openqa = fedora_openqa.cli:main',
        ],
    },
    author="Fedora QA devel team",
    author_email="qa-devel@lists.fedoraproject.org",
    description="Fedora openQA job scheduler and result forwarders",
    license="GPLv3+",
    keywords="fedora openqa test qa",
    url="https://pagure.io/fedora-qa/fedora_openqa",
    packages=["fedora_openqa"],
    install_requires=INSTALLREQS,
    tests_require=open('tests.requires').read().splitlines(),
    cmdclass={'test': PyTest},
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
)
