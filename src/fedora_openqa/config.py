# Copyright Red Hat
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
CONFIG.add_section('schedule')

CONFIG.set('cli', 'log-file', '')
CONFIG.set('cli', 'log-level', 'info')

CONFIG.set('report', 'resultsdb_url', 'http://localhost:5001/api/v2.0/')
CONFIG.set('report', 'resultsdb_user', '')
CONFIG.set('report', 'resultsdb_password', '')
CONFIG.set('report', 'wiki_hostname', 'stg.fedoraproject.org')

CONFIG.set('schedule', 'arches', 'x86_64')

CONFIG.read('/etc/fedora-openqa/schedule.conf')
CONFIG.read('{0}/.config/fedora-openqa/schedule.conf'.format(os.path.expanduser('~')))

# The default set of tested images. This set can be overridden by an
# 'images.json' file in /etc/fedora-openqa or ~/.config/fedora-openqa,
# and filtered by arguments passed to `schedule.jobs_from_compose` or
# set in the configuration file.
# Refer to comments in ../images.json.sample

WANTED = [
    {
        "match": {
            "subvariant": "Server",
            "type": "boot",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "dvd",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Everything",
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
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "live-osbuild",
            "format": "iso",
            "arch": "x86_64",
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
            "subvariant": "Silverblue",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "IoT",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "BaseOS",
            "type": "dvd",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "BaseOS",
            "type": "boot",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Cloud_Base",
            "type": "qcow2",
            "format": "qcow2",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "Everything",
            "type": "boot",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "live",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "boot",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "dvd",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Cloud_Base",
            "type": "qcow2",
            "format": "qcow2",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Silverblue",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "IoT",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "ppc64le",
        },
    },
    {
        "match": {
            "subvariant": "Minimal",
            "type": "raw-xz",
            "format": "raw.xz",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "boot",
            "format": "iso",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "dvd",
            "format": "iso",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "Server",
            "type": "raw-xz",
            "format": "raw.xz",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "Workstation",
            "type": "raw-xz",
            "format": "raw.xz",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "Cloud_Base",
            "type": "qcow2",
            "format": "qcow2",
            "arch": "aarch64",
        },
    },
    {
        "match": {
            "subvariant": "IoT",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "aarch64",
        },
    }
]

# List of non-critpath package names to run update tests on.
# Dict keys are the package names, value is an iterable of the
# flavor(s) of update tests to run for that package
UPDATETL = {
    # FreeIPA-related bits
    'pki-core': ('server', 'server-upgrade'),
    'python-pyldap': ('server', 'server-upgrade'),
    # Since we have background tests, makes sense to do these
    'desktop-backgrounds': ('kde', 'workstation'),
    # printing related stuff (printing tests are gating)
    'ghostscript': ('kde', 'workstation'),
    # non-critpath container-y packages to run container tests on
    'containernetworking-plugins': ('container',),
}

for path in ('/etc/fedora-openqa',
             '{0}/.config/fedora-openqa'.format(os.path.expanduser('~'))):
    try:
        # load WANTED override config file
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

    try:
        # load UPDATETL override config file
        fname = '{0}/updatetl.json'.format(path)
        with open(fname, 'r') as fout:
            UPDATETL = json.load(fout)
    except IOError:
        # file not found
        pass

# vim: set textwidth=120 ts=8 et sw=4:
