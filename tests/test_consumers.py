# Copyright (C) Red Hat Inc.
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
# Author:   Adam Williamson <awilliam@redhat.com>

# these are all kinda inappropriate for pytest patterns
# pylint: disable=old-style-class, no-init, protected-access, no-self-use, unused-argument

"""Tests for the fedmsg consumers."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
import copy

# external imports
from fedora_messaging.api import Message
import mock
import pytest

# 'internal' imports
import fedora_openqa.consumer
from fedora_openqa.config import UPDATEWL

# Modified version of the default UPDATEWL for testing purposes
# we have to do this because we don't have any real-world cases
# for whitelisting anything but the 'server' tests yet, so we can't
# fully test the feature with the real default whitelist
MODIFIEDWL = copy.deepcopy(UPDATEWL)
MODIFIEDWL['gnome-terminal'] = ('workstation',)
MODIFIEDWL['kernel'] = None

# Passed test message
PASSMSG = Message(
    topic="org.fedoraproject.stg.openqa.job.done",
    body={
            "ARCH": "x86_64",
            "BUILD": "Fedora-Rawhide-20170207.n.0",
            "FLAVOR": "universal",
            "ISO": "Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
            "MACHINE": "64bit",
            "TEST": "install_asian_language",
            "id": 71262,
            "newbuild": None,
            "remaining": 23,
            "result": "passed"
    }
)

# Started compose message
STARTEDCOMPOSE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "compose_id": "Fedora-Atomic-25-20170206.0",
        "location": "http://kojipkgs.fedoraproject.org/compose/twoweek/Fedora-Atomic-25-20170206.0/compose",
        "status": "STARTED"
    }
)

# Doomed compose message
DOOMEDCOMPOSE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "compose_id": "Fedora-Docker-25-20170206.0",
        "location": "http://kojipkgs.fedoraproject.org/compose/Fedora-Docker-25-20170206.0/compose",
        "status": "DOOMED"
    }
)

# Finished compose message
FINISHEDCOMPOSE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "compose_id": "Fedora-Atomic-25-20170206.0",
        "location": "http://kojipkgs.fedoraproject.org/compose/twoweek/Fedora-Atomic-25-20170206.0/compose",
        "status": "FINISHED"
    }
)

# Finished incomplete compose message
FINCOMPLETE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "compose_id": "Fedora-Rawhide-20170206.n.0",
        "location": "http://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170206.n.0/compose",
        "status": "FINISHED_INCOMPLETE"
    }
)

# Critpath update creation message. These are huge, so this is heavily
# edited.
CRITPATHCREATE = Message(
    topic="org.fedoraproject.prod.bodhi.update.request.testing",
    body={
        "agent": "msekleta",
        "update": {
            "alias": "FEDORA-2017-ea07abb5d5",
            "builds": [
                {
                    "epoch": 0,
                    "nvr": "systemd-231-14.fc24",
                    "signed": False
                }
            ],
            "critpath": True,
            "release": {
                "branch": "f24",
                "dist_tag": "f24",
                "id_prefix": "FEDORA",
                "long_name": "Fedora 24",
                "name": "F24",
                "version": "24"
            },
        },
    }
)

# Non-critpath, non-whitelisted update creation message
NONCRITCREATE = copy.deepcopy(CRITPATHCREATE)
NONCRITCREATE.body['update']['critpath'] = False

# Non-critpath, one-flavor-whitelisted update creation message
WLCREATE = copy.deepcopy(CRITPATHCREATE)
WLCREATE.body['update']['critpath'] = False
WLCREATE.body['update']['builds'] = [{"epoch": 0, "nvr": "freeipa-4.4.4-1.fc24", "signed": False}]

# Critpath EPEL update creation message
EPELCREATE = copy.deepcopy(CRITPATHCREATE)
EPELCREATE.body['update']['release']['id_prefix'] = 'FEDORA-EPEL'

# Critpath update edit message
CRITPATHEDIT = Message(
    topic="org.fedoraproject.prod.bodhi.update.edit",
    body={
        "agent": "hobbes1069",
        "update": {
            "alias": "FEDORA-2017-e6d7184200",
            "critpath": True,
            "release": {
                "branch": "f24",
                "dist_tag": "f24",
                "id_prefix": "FEDORA",
                "long_name": "Fedora 24",
                "name": "F24",
                "version": "24"
            },
        },
    }
)

# Non-critpath, non-whitelisted update edit message
NONCRITEDIT = copy.deepcopy(CRITPATHEDIT)
NONCRITEDIT.body['update']['critpath'] = False

# Non-critpath, two-flavors-whitelisted update edit message
WLEDIT = copy.deepcopy(CRITPATHEDIT)
WLEDIT.body['update']['critpath'] = False
WLEDIT.body['update']['builds'] = [
    {"epoch": 0, "nvr": "freeipa-4.4.4-1.fc26", "signed": False},
    {"epoch": 0, "nvr": "gnome-terminal-3.24.1-1.fc24", "signed": False},
]

# Non-critpath, all-flavors-whitelisted update edit message
WLALLEDIT = copy.deepcopy(CRITPATHEDIT)
WLALLEDIT.body['update']['critpath'] = False
WLALLEDIT.body['update']['builds'] = [{"epoch": 0, "nvr": "kernel-4.10.12-100.fc24", "signed": False}]

# Critpath EPEL update edit message
EPELEDIT = copy.deepcopy(CRITPATHEDIT)
EPELEDIT.body['update']['release']['id_prefix'] = 'FEDORA-EPEL'

# initialize a few test consumers with different configs
PRODCONF = {
    'consumer_config': {
        'do_report':True,
        'openqa_hostname':'openqa.fedoraproject.org',
        'openqa_baseurl':'https://openqa.fedoraproject.org',
        'wiki_hostname':'fedoraproject.org',
        'resultsdb_url':'http://resultsdb01.qa.fedoraproject.org/resultsdb_api/api/v2.0/',
    }
}
STGCONF = {
    'consumer_config': {
        'do_report':False,
        'openqa_hostname':'openqa.stg.fedoraproject.org',
        'openqa_baseurl':'https://openqa.stg.fedoraproject.org',
        'wiki_hostname':'stg.fedoraproject.org',
        'resultsdb_url':'http://resultsdb-stg01.qa.fedoraproject.org/resultsdb_api/api/v2.0/',
    }
}
TESTCONF = {
    'consumer_config': {
        'do_report':False,
        'openqa_hostname':'localhost',
        'openqa_baseurl':'https://localhost',
        'wiki_hostname':'stg.fedoraproject.org',
        'resultsdb_url':'http://localhost:5001/api/v2.0/',
    }
}

with mock.patch.dict('fedora_messaging.config.conf', PRODCONF):
    PRODSCHED = fedora_openqa.consumer.OpenQAScheduler()
    PRODWIKI = fedora_openqa.consumer.OpenQAWikiReporter()
    PRODRDB = fedora_openqa.consumer.OpenQAResultsDBReporter()
with mock.patch.dict('fedora_messaging.config.conf', STGCONF):
    STGSCHED = fedora_openqa.consumer.OpenQAScheduler()
    STGWIKI = fedora_openqa.consumer.OpenQAWikiReporter()
    STGRDB = fedora_openqa.consumer.OpenQAResultsDBReporter()
with mock.patch.dict('fedora_messaging.config.conf', TESTCONF):
    TESTSCHED = fedora_openqa.consumer.OpenQAScheduler()
    TESTWIKI = fedora_openqa.consumer.OpenQAWikiReporter()
    TESTRDB = fedora_openqa.consumer.OpenQAResultsDBReporter()

PRODS = (PRODWIKI, PRODRDB, PRODSCHED)
STGS = (STGWIKI, STGRDB, STGSCHED)
# we don't include TESTSCHED as its values are hardcoded
TESTS = (TESTWIKI, TESTRDB)


@pytest.mark.usefixtures("ffmock")
class TestConsumers:
    """Tests for the consumers."""

    @mock.patch('fedora_openqa.consumer.UPDATEWL', MODIFIEDWL)
    @mock.patch('fedora_openqa.schedule.jobs_from_compose', return_value=('somecompose', [1]), autospec=True)
    @mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1], autospec=True)
    @pytest.mark.parametrize(
        "consumer,oqah",
        [
            (PRODSCHED, 'openqa.fedoraproject.org'),
            (STGSCHED, 'openqa.stg.fedoraproject.org'),
            (TESTSCHED, 'localhost'),
        ]
    )
    @pytest.mark.parametrize(
        "message,flavors",
        [
            # For 'flavors': 'False' means no jobs should be created. For
            # compose scheduling, any other value just means "jobs should
            # be created". For update scheduling, any value but 'False'
            # means "jobs should be created, and this is the expected value
            # of the 'flavors' kwarg to the fake_update call" (remember,
            # None means "run tests for all flavors").
            (STARTEDCOMPOSE, False),
            (DOOMEDCOMPOSE, False),
            (FINISHEDCOMPOSE, True),
            (FINCOMPLETE, True),
            # for all critpath updates we should schedule for all flavors
            (CRITPATHCREATE, None),
            (CRITPATHEDIT, None),
            (NONCRITCREATE, False),
            (NONCRITEDIT, False),
            (EPELCREATE, False),
            (EPELEDIT, False),
            # WLCREATE contains only a 'server'-whitelisted package
            (WLCREATE, ['server', 'server-upgrade']),
            # WLEDIT contains both 'server' and 'workstation'-whitelisted
            # packages
            (WLEDIT, ['server', 'server-upgrade', 'workstation']),
            # WLALLEDIT contains an 'all flavors'-whitelisted package
            (WLALLEDIT, None),
        ]
    )
    def test_scheduler(self, fake_update, fake_schedule, consumer, oqah, message, flavors):
        """Test the job scheduling consumers do their thing. The
        parametrization pairs are:
        1. (consumer, expected openQA hostname)
        2. (fedmsg, job creation? / expected flavors value (see above)
        If jobs are expected, we check the schedule function was hit
        and that the hostname is as expected. If jobs aren't expected,
        we check the schedule function was not hit.
        """
        consumer(message)
        if flavors is False:
            assert fake_schedule.call_count + fake_update.call_count == 0
        else:
            assert fake_schedule.call_count + fake_update.call_count == 1
            if fake_schedule.call_count == 1:
                assert fake_schedule.call_args[1]['openqa_hostname'] == oqah
            else:
                assert fake_update.call_args[1]['openqa_hostname'] == oqah
                assert fake_update.call_args[1]['flavors'] == flavors
        #fake_schedule.reset_mock()


    @mock.patch('fedora_openqa.report.wiki_report', autospec=True)
    @pytest.mark.parametrize(
        "consumer,expected",
        [
            (PRODWIKI, {'report': True, 'oqah': 'openqa.fedoraproject.org', 'wikih': 'fedoraproject.org'}),
            (STGWIKI, {'report': False, 'oqah': 'openqa.stg.fedoraproject.org', 'wikih': 'stg.fedoraproject.org'}),
            (TESTWIKI, {'report': False, 'oqah': 'localhost', 'wikih': 'stg.fedoraproject.org'}),
        ]
    )
    def test_wiki_default(self, fake_report, consumer, expected):
        """Test we appropriately attempt to report results for a passed
        test to the wiki, with expected default values, for each wiki
        consumer. The parametrization tuples specify the expected args
        to the wiki_report call for each consumer. We compare against
        the call_args of the mock.
        """
        consumer(PASSMSG)
        assert fake_report.call_count == 1
        assert fake_report.call_args[1]['jobs'] == [71262]
        assert fake_report.call_args[1]['do_report'] == expected['report']
        assert fake_report.call_args[1]['openqa_hostname'] == expected['oqah']
        assert fake_report.call_args[1]['wiki_hostname'] == expected['wikih']
        fake_report.reset_mock()


    @mock.patch('fedora_openqa.report.resultsdb_report', autospec=True)
    @pytest.mark.parametrize(
        "consumer,expected",
        [
            (
                PRODRDB,
                {
                    'report': True,
                    'oqah': 'openqa.fedoraproject.org',
                    'rdburl': 'http://resultsdb01.qa.fedoraproject.org/resultsdb_api/api/v2.0/'
                }
            ),
            (
                STGRDB,
                {
                    'report': False,
                    'oqah': 'openqa.stg.fedoraproject.org',
                    'rdburl': 'http://resultsdb-stg01.qa.fedoraproject.org/resultsdb_api/api/v2.0/'
                }
            ),
            (
                TESTRDB,
                {
                    'report': False,
                    'oqah': 'localhost',
                    'rdburl': 'http://localhost:5001/api/v2.0/'
                }
            ),
        ]
    )
    def test_resultsdb_default(self, fake_report, consumer, expected):
        """Test we appropriately attempt to report results for a passed
        test to ResultsDB, with expected default values. Works much the
        same as test_wiki_default; the parametrization tuples specify
        the expected resultsdb_report args for each consumer.
        """
        consumer(PASSMSG)
        assert fake_report.call_count == 1
        assert fake_report.call_args[1]['jobs'] == [71262]
        assert fake_report.call_args[1]['do_report'] == expected['report']
        assert fake_report.call_args[1]['openqa_hostname'] == expected['oqah']
        assert fake_report.call_args[1]['resultsdb_url'] == expected['rdburl']
        fake_report.reset_mock()

# vim: set textwidth=120 ts=8 et sw=4:
