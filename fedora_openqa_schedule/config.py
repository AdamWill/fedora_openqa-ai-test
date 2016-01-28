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
# the format of images.json very closely, and this set can be
# overridden by an 'images.json' file in /etc/fedora-openqa or
# ~/.config/fedora-openqa. We parse through the images.json and for
# each image dict, if all the items in the wanted dict match, we
# take that image. An important exception is the "score" item, which
# does not appear in images.json and is not used for matching; rather,
# we use it to decide which images to run the 'universal' tests with.
# For each arch that has universal tests, the found image with the
# highest score is used. If no image with a score > 0 is found, the
# universal tests are skipped. If score is not specified the image is
# considered to have a score of 0.
WANTED = {
    "Server": {
        "x86_64": [
            {
                "type": "boot",
                "format": "iso",
                "score": 6,
            },
            {
                "type": "dvd",
                "format": "iso",
                "score": 10,
            },
        ],
        "i386": [
            {
                "type": "boot",
                "format": "iso",
                "score": 6,
            },
            {
                "type": "dvd",
                "format": "iso",
                "score": 10,
            },
        ],
    },
    "Everything": {
        "x86_64": [
            {
                "type": "boot",
                "format": "iso",
                "score": 8,
            },
        ],
        "i386": [
            {
                "type": "boot",
                "format": "iso",
                "score": 8,
            },
        ],
    },
    "Workstation": {
        "x86_64": [
            {
                "type": "live",
                "format": "iso",
            },
        ],
        "i386": [
            {
                "type": "live",
                "format": "iso",
            },
        ],
    },
    "KDE": {
        "x86_64": [
            {
                "type": "live",
                "format": "iso",
            },
        ],
        "i386": [
            {
                "type": "live",
                "format": "iso",
            },
        ],
    },
    "Cloud-Atomic": {
        "x86_64": [
            {
                "type": "boot",
                "format": "iso",
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
