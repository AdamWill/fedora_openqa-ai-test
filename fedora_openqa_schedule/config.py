# Copyright (C) 2015 Red Hat
#
# This file is part of fedora-openqa-schedule.
#
# fedora-openqa-schedule is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Adam Williamson <awilliam@redhat.com>

"""Config file handling: parses config and provides it as CONFIG."""

# Standard libraries
import json
import os.path

# External dependencies
from six.moves import configparser


class ConfigError(Exception):
    """Raised when there's an error in a config file."""
    pass

# Read in config from /etc/fedora-openqa/schedule.conf or
# ~/.config/fedora-openqa/schedule.conf after setting some default
# values.
CONFIG = configparser.ConfigParser()
CONFIG.add_section('cli')
CONFIG.add_section('report')
CONFIG.set('cli', 'log-file', '')
CONFIG.set('cli', 'log-level', 'info')
CONFIG.set('report', 'submit_wiki', 'true')
CONFIG.set('report', 'submit_resultsdb', 'true')
CONFIG.set('report', 'openqa_url', 'http://localhost')
CONFIG.set('report', 'resultsdb_url', 'http://localhost:5001/api/v2.0/')
CONFIG.set('report', 'wiki_url', 'https://fedoraproject.org/wiki')
CONFIG.set('report', 'wiki_stg_url', 'https://stg.fedoraproject.org/wiki')
CONFIG.read('/etc/fedora-openqa/schedule.conf')
CONFIG.read('{0}/.config/fedora-openqa/schedule.conf'.format(os.path.expanduser('~')))

# The default set of tested images. This set can be overridden by an
# 'images.json' file in /etc/fedora-openqa or ~/.config/fedora-openqa.

# The format is a list of dicts. Each dict represents a single image
# we want to test. The list is compared against the list of image
# dicts fedfind returns for the release being tested. One of the items
# in the image dict is itself a dict called 'match'. This dict
# determines whether the image "matches": if all the items in this
# "match" dict match the items in the fedfind image dict, we take that
# image.

# The other items in the image dict here are not used for matching,
# but instead influence the behaviour of the scheduler.

# The "score" item is used to decide which images to run the universal
# tests with. For each arch that has universal tests, the found image
# with the highest score is used. If no image with a score > 0 is
# found, the universal tests are skipped. If score is not specified
# the image is considered to have a score of 0.

# If "dkboot" is set to True, scheduler also downloads kernel and initrd
# files for specified architecture and then schedules job to run in Direct
# Kernel Boot mode. Default value (used when dkboot item is not specified)
# is False.

WANTED = [
    {
        "match": {
            "subvariant": "Server",
            "type": "boot",
            "format": "iso",
            "arch": "x86_64",
        },
        "score": 6,
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "dvd",
            "format": "iso",
            "arch": "x86_64",
        },
        "score": 10,
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "boot",
            "format": "iso",
            "arch": "i386",
        },
        "score": 6,
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "dvd",
            "format": "iso",
            "arch": "i386",
        },
        "score": 10,
    },
    {
        "match": {
            "subvariant": "Everything",
            "type": "boot",
            "format": "iso",
            "arch": "x86_64",
        },
        "score": 8,
    },
    {
        "match": {
            "subvariant": "Everything",
            "type": "boot",
            "format": "iso",
            "arch": "i386",
        },
        "score": 8,
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "live",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "boot",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "live",
            "format": "iso",
            "arch": "i386",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "boot",
            "format": "iso",
            "arch": "i386",
        },
    },
    {
        "match": {
            "subvariant": "KDE",
            "type": "live",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "KDE",
            "type": "live",
            "format": "iso",
            "arch": "i386",
        },
    },
    {
        "match": {
            "subvariant": "Minimal",
            "type": "raw-xz",
            "format": "raw.xz",
            "arch": "armhfp",
        },
        "dkboot": True,
    },
    {
        "match": {
            "subvariant": "Atomic",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "x86_64",
        },
    },
]

for path in ('/etc/fedora-openqa',
             '{0}/.config/fedora-openqa'.format(os.path.expanduser('~'))):
    try:
        fname = '{0}/images.json'.format(path)
        with open(fname, 'r') as fout:
            WANTED = json.load(fout)
            try:
                WANTED.keys()
                raise ConfigError("{0} is in old format (dict, not list)!".format(fname))
            except AttributeError:
                pass
    except IOError:
        # file not found
        pass
