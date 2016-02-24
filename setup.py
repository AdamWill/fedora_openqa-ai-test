import glob
import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below. Stolen from
# https://pythonhosted.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), "..", fname)).read()

# Allow modification of systemd install location via env var.
SYSTEMDUNITPATH = os.getenv("SYSTEMDUNITPATH", '/usr/lib/systemd/system')

setup(
    name = "fedora-openqa",
    version = "1.0",
    entry_points = {
        'console_scripts': [
            'fedora-openqa-schedule = fedora_openqa_schedule.cli:main',
            'fedora-openqa-consumer = fedora_openqa_schedule.consumer:main',
        ],
    },
    author = "Fedora QA devel team",
    author_email = "qa-devel@lists.fedoraproject.org",
    description = "Fedora openQA scheduler",
    license = "GPLv3+",
    keywords = "fedora openqa test qa",
    url = "https://bitbucket.org/rajcze/openqa_fedora_tools",
    packages = ["fedora_openqa_schedule"],
    install_requires = ['fedfind>=1.5', 'openqa-client', 'setuptools', 'six'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
    data_files=[
        (SYSTEMDUNITPATH, glob.glob('systemd/*.service')),
    ],
)
