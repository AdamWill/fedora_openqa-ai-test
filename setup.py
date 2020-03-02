from os import path
from setuptools import setup

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONGDESC = f.read()

setup(
    name="fedora_openqa",
    version="3.1.0",
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
    package_dir={"": "src"},
    install_requires=open('install.requires').read().splitlines(),
    python_requires="!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",
    long_description=LONGDESC,
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
)
