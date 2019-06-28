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
CONFIG.add_section('consumers')

CONFIG.set('cli', 'log-file', '')
CONFIG.set('cli', 'log-level', 'info')

CONFIG.set('report', 'resultsdb_url', 'http://localhost:5001/api/v2.0/')
CONFIG.set('report', 'wiki_hostname', 'stg.fedoraproject.org')

CONFIG.read('/etc/fedora-openqa/schedule.conf')
CONFIG.read('{0}/.config/fedora-openqa/schedule.conf'.format(os.path.expanduser('~')))

# The default set of tested images. This set can be overridden by an
# 'images.json' file in /etc/fedora-openqa or ~/.config/fedora-openqa.
# Refer to comments in ../images.json.sample

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
    # 'Atomic' subvariant was renamed to 'AtomicHost' from F28 onward,
    # when there are no more F28 images being produced, we can drop
    # this here and elsewhere
    {
        "match": {
            "subvariant": "Atomic",
            "type": "dvd-ostree",
            "format": "iso",
            "arch": "x86_64",
        },
    },
    {
        "match": {
            "subvariant": "AtomicHost",
            "type": "dvd-ostree",
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
]

# Whitelist of non-critpath package names to run update tests on.
# Dict keys are the package names, value is either an iterable of the
# flavor(s) of update tests to run for that package or can just be
# None (or anything else false-y) which means "run all the flavors".
UPDATEWL = {
    # FreeIPA-related bits
    '389-ds': ('server', 'server-upgrade'),
    '389-ds-base': ('server', 'server-upgrade'),
    'bind': ('server', 'server-upgrade'),
    'bind-dyndb-ldap': ('server', 'server-upgrade'),
    'certmonger': ('server', 'server-upgrade'),
    'ding-libs': ('server', 'server-upgrade'),
    'freeipa': ('server', 'server-upgrade'),
    'httpd': ('server', 'server-upgrade'),
    'krb5-server': ('server', 'server-upgrade'),
    'pki-core': ('server', 'server-upgrade'),
    'sssd': ('server', 'server-upgrade'),
    'tomcat': ('server', 'server-upgrade'),
    'python-ldap': ('server', 'server-upgrade'),
    'python-pyldap': ('server', 'server-upgrade'),
    'softhsm': ('server', 'server-upgrade'),
    'libldb': ('server', 'server-upgrade'),
    'samba': ('server', 'server-upgrade'),
    # this is involved in FreeIPA and of course regular use too. It
    # is missing from Bodhi's stale critpath definition
    'authselect': None,
    # Cockpit-related bits
    'cockpit': ('server',),
    # PostgreSQL is a release-blocking server role
    'postgresql': ('server',),
    # Bits of GNOME that aren't in critpath
    'gnome-software': ('workstation', 'workstation-live-iso'),
    'accountsservice': ('workstation', 'workstation-upgrade', 'workstation-live-iso'),
    'gnome-initial-setup': ('workstation-live-iso',),
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
        # load UPDATEWL override config file
        fname = '{0}/updatewl.json'.format(path)
        with open(fname, 'r') as fout:
            UPDATEWL = json.load(fout)
    except IOError:
        # file not found
        pass

# vim: set textwidth=120 ts=8 et sw=4:
