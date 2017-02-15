import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below. Stolen from
# https://pythonhosted.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "fedora_openqa",
    version = "3.0.0",
    entry_points = {
        'console_scripts': [
            'fedora-openqa = fedora_openqa.cli:main',
        ],
        'moksha.consumer': [
            'fedora_openqa.scheduler.prod = fedora_openqa.consumer:OpenQAProductionScheduler',
            'fedora_openqa.scheduler.stg = fedora_openqa.consumer:OpenQAStagingScheduler',
            'fedora_openqa.scheduler.test = fedora_openqa.consumer:OpenQATestScheduler',
            'fedora_openqa.wiki.reporter.prod = fedora_openqa.consumer:OpenQAProductionWikiReporter',
            'fedora_openqa.wiki.reporter.stg = fedora_openqa.consumer:OpenQAStagingWikiReporter',
            'fedora_openqa.wiki.reporter.test = fedora_openqa.consumer:OpenQATestWikiReporter',
            'fedora_openqa.resultsdb.reporter.prod = fedora_openqa.consumer:OpenQAProductionResultsDBReporter',
            'fedora_openqa.resultsdb.reporter.stg = fedora_openqa.consumer:OpenQAStagingResultsDBReporter',
            'fedora_openqa.resultsdb.reporter.test = fedora_openqa.consumer:OpenQATestResultsDBReporter',
        ],
    },
    author = "Fedora QA devel team",
    author_email = "qa-devel@lists.fedoraproject.org",
    description = "Fedora openQA job scheduler and result forwarders",
    license = "GPLv3+",
    keywords = "fedora openqa test qa",
    url = "https://pagure.io/fedora-qa/fedora_openqa",
    packages = ["fedora_openqa"],
    install_requires = ['fedfind>=2.5.0', 'fedmsg', 'openqa-client>=1.1', 'setuptools',
                        'six', 'resultsdb_api', 'resultsdb_conventions>=2.0.0'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
)
