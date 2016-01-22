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
CONFIG.add_section('schedule')
CONFIG.set('cli', 'log-file', '')
CONFIG.set('cli', 'log-level', 'info')
CONFIG.set('report', 'submit', 'true')
CONFIG.set('report', 'jobs-wait', '360')
CONFIG.set('schedule', 'iso-path', '/var/lib/openqa/factory/iso/')
CONFIG.set('schedule', 'compose-wait', '480')
CONFIG.set('schedule', 'imagetype', 'boot live dvd canned')
CONFIG.set('schedule', 'arches', 'x86_64 i386')
CONFIG.set('schedule', 'payload', 'cloud_atomic server generic workstation kde')
CONFIG.set('schedule', 'persistent', '/var/tmp/openqa_watcher.json')
CONFIG.read('/etc/fedora-openqa/schedule.conf')
CONFIG.read('{0}/.config/fedora-openqa/schedule.conf'.format(os.path.expanduser('~')))
