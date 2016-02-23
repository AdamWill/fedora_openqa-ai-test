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
import os.path

# External dependencies
from six.moves import configparser

# Read in config from /etc/fedora-openqa/schedule.conf or
# ~/.config/fedora-openqa/schedule.conf after setting some default
# values.
CONFIG = configparser.ConfigParser()
CONFIG.add_section('cli')
CONFIG.add_section('report')
CONFIG.set('cli', 'log-file', '')
CONFIG.set('cli', 'log-level', 'info')
CONFIG.set('report', 'submit', 'true')
CONFIG.set('report', 'jobs-wait', '360')
CONFIG.read('/etc/fedora-openqa/schedule.conf')
CONFIG.read('{0}/.config/fedora-openqa/schedule.conf'.format(os.path.expanduser('~')))

# The default set of tested images. The format intentionally follows
# the format of images.json closely, and this set can be overridden by
# an 'images.json' file in /etc/fedora-openqa or
# ~/.config/fedora-openqa.

# There is one level added to this dict compared to images.json.
# images.json is a dict of dicts representing "variants". Each variant
# is a dict of lists representing arches. Each arch list contains
# dicts which each contain the properties of a single image as simple
# strings.

# In our dict, things are same until we reach the image level. Again,
# each item in the list for a given arch within a given variant is a
# dict for a single image. However, one of the items in the image dict
# is itself a dict, called 'match'. This dict determines whether the
# image "matches": if all the items in this "match" dict match the
# items in the image dict from the upstream metadata, we take that
# image.

# For most keys we simply perform a Python 'equality' match. There is
# one exception: the "payload" key is special. It doesn't exist
# upstream. When the 'match' dict contains a 'payload' key, we derive
# a payload from the upstream "path" key and compare against that.
# This is necessary to identify, for instance, "the KDE live image"
# for a given arch in the Spins variant. There is no key in the
# upstream metadata which can be used for this without some sort of
# interpretation like this. The match is performed by extracting the
# filename from the upstream 'path' and splitting it with '-' as the
# separator; we then see if any of the resulting elements matches the
# payload (case-insensitively).

# The other items in the image dict here are not used for matching,
# but instead influence the behaviour of the scheduler.

# The "score" item is used to decide which images to run the universal
# tests with. For each arch that has universal tests, the found image
# with the highest score is used. If no image with a score > 0 is
# found, the universal tests are skipped. If score is not specified
# the image is considered to have a score of 0.

WANTED = {
    "Server": {
        "x86_64": [
            {
                "match": {
                    "type": "boot",
                    "format": "iso",
                },
                "score": 6,
            },
            {
                "match": {
                    "type": "dvd",
                    "format": "iso",
                },
                "score": 10,
            },
        ],
        "i386": [
            {
                "match": {
                    "type": "boot",
                    "format": "iso",
                },
                "score": 6,
            },
            {
                "match": {
                    "type": "dvd",
                    "format": "iso",
                },
                "score": 10,
            },
        ],
    },
    "Everything": {
        "x86_64": [
            {
                "match": {
                    "type": "boot",
                    "format": "iso",
                },
                "score": 8,
            },
        ],
        "i386": [
            {
                "match": {
                    "type": "boot",
                    "format": "iso",
                },
                "score": 8,
            },
        ],
    },
    "Workstation": {
        "x86_64": [
            {
                "match": {
                    "type": "live",
                    "format": "iso",
                },
            },
        ],
        "i386": [
            {
                "match": {
                    "type": "live",
                    "format": "iso",
                },
            },
        ],
    },
    "Spins": {
        "x86_64": [
            {
                "match": {
                    "payload": "KDE",
                    "type": "live",
                    "format": "iso",
                },
            },
        ],
        "i386": [
            {
                "match": {
                    "payload": "KDE",
                    "type": "live",
                    "format": "iso",
                },
            },
        ],
    },
    "Atomic": {
        "x86_64": [
            {
                "match": {
                    "type": "boot",
                    "format": "iso",
                },
            },
        ],
    },
}

for path in ('/etc/fedora-openqa',
             '{0}/.config/fedora-openqa'.format(os.path.expanduser('~'))):
    try:
        with open('{0}/images.json'.format(path), 'r') as fout:
            WANTED = json.load(fout)
    except IOError:
        # file not found
        pass
