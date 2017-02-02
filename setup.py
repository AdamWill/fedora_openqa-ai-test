import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below. Stolen from
# https://pythonhosted.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), "..", fname)).read()

setup(
    name = "fedora-openqa",
    version = "2.0",
    entry_points = {
        'console_scripts': [
            'fedora-openqa-schedule = fedora_openqa_schedule.cli:main',
        ],
        'moksha.consumer': [
            'fedora_openqa_schedule.consumer = fedora_openqa_schedule.consumer:OpenQAConsumer',
            'fedora_openqa_schedule.wiki.consumer.prod = fedora_openqa_schedule.consumer:OpenQAProductionWikiConsumer',
            'fedora_openqa_schedule.wiki.consumer.stg = fedora_openqa_schedule.consumer:OpenQAStagingWikiConsumer',
            'fedora_openqa_schedule.wiki.consumer.test = fedora_openqa_schedule.consumer:OpenQATestWikiConsumer',
        ],
    },
    author = "Fedora QA devel team",
    author_email = "qa-devel@lists.fedoraproject.org",
    description = "Fedora openQA scheduler",
    license = "GPLv3+",
    keywords = "fedora openqa test qa",
    url = "https://bitbucket.org/rajcze/openqa_fedora_tools",
    packages = ["fedora_openqa_schedule"],
    install_requires = ['fedfind>=2.5.0', 'fedmsg', 'openqa-client>=1.1', 'setuptools',
                        'six', 'resultsdb_api', 'resultsdb_conventions'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
)
