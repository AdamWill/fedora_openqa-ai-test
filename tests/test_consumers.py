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
# Author:   Adam Williamson <awilliam@redhat.com>

# these are all kinda inappropriate for pytest patterns
# pylint: disable=old-style-class, no-init, protected-access, no-self-use, unused-argument

"""Tests for the fedmsg consumers."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
import copy
from unittest import mock

# external imports
from fedora_messaging.api import Message
import pytest

# 'internal' imports
import fedora_openqa.consumer

# Passed test message (ZMQ->AMQP bridge style with whole fedmsg as
# 'body')
PASSMSG = Message(
    topic="org.fedoraproject.stg.openqa.job.done",
    body={
        'msg_id': "2017-f059828d-0969-4545-be7a-db8334f6a71f",
        'msg': {
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

# Finished incomplete compose message (ZMQ->AMQP bridge style with
# whole fedmsg as 'body')
FINCOMPLETE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "msg_id": "2017-f059828d-0969-4545-be7a-db8334f6a71f",
        "msg": {
            "compose_id": "Fedora-Rawhide-20170206.n.0",
            "location": "http://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170206.n.0/compose",
            "status": "FINISHED_INCOMPLETE"
        }
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

# Non-critpath, non-listed update creation message
NONCRITCREATE = copy.deepcopy(CRITPATHCREATE)
NONCRITCREATE.body['update']['critpath'] = False

# Non-critpath, one-flavor-listed update creation message
TLCREATE = copy.deepcopy(CRITPATHCREATE)
TLCREATE.body['update']['critpath'] = False
TLCREATE.body['update']['builds'] = [{"epoch": 0, "nvr": "freeipa-4.4.4-1.fc24", "signed": False}]

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

# Non-critpath, non-listed update edit message
NONCRITEDIT = copy.deepcopy(CRITPATHEDIT)
NONCRITEDIT.body['update']['critpath'] = False

# Non-critpath, two-flavors-listed update edit message
TLEDIT = copy.deepcopy(CRITPATHEDIT)
TLEDIT.body['update']['critpath'] = False
TLEDIT.body['update']['builds'] = [
    {"epoch": 0, "nvr": "freeipa-4.4.4-1.fc26", "signed": False},
    {"epoch": 0, "nvr": "gnome-initial-setup-3.24.1-1.fc24", "signed": False},
]

# Non-critpath, all-flavors-listed update edit message
TLALLEDIT = copy.deepcopy(CRITPATHEDIT)
TLALLEDIT.body['update']['critpath'] = False
TLALLEDIT.body['update']['builds'] = [{"epoch": 0, "nvr": "authselect-4.10.12-100.fc24", "signed": False}]

# Critpath EPEL update edit message
EPELEDIT = copy.deepcopy(CRITPATHEDIT)
EPELEDIT.body['update']['release']['id_prefix'] = 'FEDORA-EPEL'

# Bodhi 'update ready for testing' message which is a re-trigger
# request for a Fedora update
RETRIGGER = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": True,
        "artifact": {
          "release": "f34",
          "type": "koji-build-group",
          "builds": [
            {
              "nvr": "gdb-11.1-5.fc34",
              "task_id": 78709925,
              "scratch": False,
              "component": "gdb",
              "type": "koji-build",
              "id": 1854854,
              "issuer": "kevinb"
            }
          ],
          "repository": "https://bodhi.fedoraproject.org/updates/FEDORA-2021-53a7dfa185",
          "id": "FEDORA-2021-53a7dfa185-bb4a8e2be6997eb20655fa079af87470fe416415"
        },
        "contact": {
          "docs": "https://docs.fedoraproject.org/en-US/ci/",
          "team": "Fedora CI",
          "email": "admin@fp.o",
          "name": "Bodhi"
        },
        "version": "0.2.2",
        "agent": "adamwill",
        "generated_at": "2021-11-12T22:25:12.966558Z"
    }
)

# Bodhi 'update ready for testing' message which is not a re-trigger
# request
NONRETRIGGER = copy.deepcopy(RETRIGGER)
NONRETRIGGER.body["re-trigger"] = False
NONRETRIGGER.body["agent"] = "bodhi"

# Mock Bodhi API response for FEDORA-2021-53a7dfa185
NONRETRIGGERBODHI = {
    "update": {
        "alias": "FEDORA-2021-53a7dfa185",
        "critpath": True,
        "release": {
            "branch": "f34",
            "dist_tag": "f34",
            "id_prefix": "FEDORA",
            "long_name": "Fedora 34",
            "name": "F34",
            "version": "34"
        },
    },
}

# Bodhi 'update ready for testing' message which is a re-trigger
# request, but not for a regular Fedora package update
NONFRETRIGGER = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": True,
        "artifact": {
          "release": "epel8",
          "type": "koji-build-group",
          "builds": [
            {
              "nvr": "libpinyin-epel-2.2.0-2.el8",
              "task_id": 78921389,
              "scratch": False,
              "component": "libpinyin-epel",
              "type": "koji-build",
              "id": 1856264,
              "issuer": "tdawson"
            }
          ],
          "repository": "https://bodhi.fedoraproject.org/updates/FEDORA-EPEL-2021-049da15976",
          "id": "FEDORA-EPEL-2021-049da15976-37a14b6e2476318d8338b1aa4a5a3190428eb328"
        },
        "contact": {
          "docs": "https://docs.fedoraproject.org/en-US/ci/",
          "team": "Fedora CI",
          "email": "admin@fp.o",
          "name": "Bodhi"
        },
        "version": "0.2.2",
        "agent": "tdawson",
        "generated_at": "2021-11-17T01:41:15.438773Z"
    }
)

# Bodhi 'update ready for testing' message for ELN, which we should
# ignore
ELNREADY = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": False,
        "artifact": {
          "release": "eln",
          "type": "koji-build-group",
          "builds": [
            {
              "component": "plasma-systemsettings",
              "id": 1959017,
              "issuer": "distrobuildsync-eln/jenkins-continuous-infra.apps.ci.centos.org",
              "nvr": "plasma-systemsettings-5.24.4-1.eln118",
              "scratch": False,
              "task_id": 86428034,
              "type": "koji-build"
            }
          ],
          "repository": "https://bodhi.fedoraproject.org/updates/FEDORA-2022-34ddfc814f",
          "id": "FEDORA-2022-34ddfc814f-143513cf0c5a497b7eb940aa24879aba870fc111"
        },
        "contact": {
          "docs": "https://docs.fedoraproject.org/en-US/ci/",
          "team": "Fedora CI",
          "email": "admin@fp.o",
          "name": "Bodhi"
        },
        "version": "0.2.2",
        "agent": "bodhi",
        "generated_at": "2022-04-30T04:40:03.670552Z"
    }
)

# Successful FCOS build message
FCOSBUILD = Message(
    topic="org.fedoraproject.prod.coreos.build.state.change",
    body={
        "build_id": "36.20211123.91.0",
        "stream": "rawhide",
        "basearch": "x86_64",
        "build_dir": "https://builds.coreos.fedoraproject.org/prod/streams/rawhide/builds/36.20211123.91.0/x86_64",
        "state": "FINISHED",
        "result": "SUCCESS"
    }
)
# Not "finished" FCOS build message
FCOSBUILDNOTF = copy.deepcopy(FCOSBUILD)
FCOSBUILDNOTF.body["state"] = "STARTED"
# Not "successful" FCOS build message
FCOSBUILDNOTS = copy.deepcopy(FCOSBUILD)
FCOSBUILDNOTS.body["result"] = "FAILURE"

# initialize a few test consumers with different configs
PRODCONF = {
    'consumer_config': {
        'do_report':True,
        'openqa_hostname':'openqa.fedoraproject.org',
        'openqa_baseurl':'https://openqa.fedoraproject.org',
        'wiki_hostname':'fedoraproject.org',
        'resultsdb_url':'http://resultsdb01.qa.fedoraproject.org/resultsdb_api/api/v2.0/',
        'update_arches':["x86_64"]
    }
}
STGCONF = {
    'consumer_config': {
        'do_report':False,
        'openqa_hostname':'openqa.stg.fedoraproject.org',
        'openqa_baseurl':'https://openqa.stg.fedoraproject.org',
        'wiki_hostname':'stg.fedoraproject.org',
        'resultsdb_url':'http://resultsdb-stg01.qa.fedoraproject.org/resultsdb_api/api/v2.0/',
        'update_arches':["x86_64", "ppc64le"]
    }
}
TESTCONF = {
    'consumer_config': {
        'do_report':False,
        'openqa_hostname':'localhost',
        'openqa_baseurl':'https://localhost',
        'wiki_hostname':'stg.fedoraproject.org',
        'resultsdb_url':'http://localhost:5001/api/v2.0/',
        'update_arches':["x86_64", "ppc64le"]
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

    @mock.patch('fedora_openqa.schedule.jobs_from_compose', return_value=('somecompose', [1]), autospec=True)
    @mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1], autospec=True)
    @mock.patch('fedora_openqa.schedule.jobs_from_fcosbuild', return_value=[1], autospec=True)
    @mock.patch('fedfind.helpers.download_json', return_value=NONRETRIGGERBODHI, autospec=True)
    @pytest.mark.parametrize(
        "consumer,oqah",
        [
            (PRODSCHED, 'openqa.fedoraproject.org'),
            (STGSCHED, 'openqa.stg.fedoraproject.org'),
            (TESTSCHED, 'localhost'),
        ]
    )
    @pytest.mark.parametrize(
        "message,gotjobs,flavors,advisory,version",
        [
            # For 'flavors': 'False' means no jobs should be created. For
            # compose scheduling, any other value just means "jobs should
            # be created". For update scheduling, any value but 'False'
            # means "jobs should be created, and this is the expected value
            # of the 'flavors' kwarg to the fake_update call" (remember,
            # None means "run tests for all flavors").
            # if 'gotjobs' is True, we mock a query of existing jobs to
            # return some. otherwise, we mock it to return nothing. This
            # is for testing re-trigger request scheduling in both cases,
            # it is irrelevant to 'new/edited update' and 'new compose'
            # message handling.
            # if "advisory" and/or "version" is a string, we'll check
            # that value is used in the update scheduling request. This is
            # for re-trigger request handling, where we do non-trivial
            # parsing to get those values.
            (STARTEDCOMPOSE, False, False, None, None),
            (DOOMEDCOMPOSE, False, False, None, None),
            (FINISHEDCOMPOSE, False, True, None, None),
            (FINCOMPLETE, False, True, None, None),
            # for all critpath updates we should schedule for all flavors
            (CRITPATHCREATE, False, None, None, None),
            (CRITPATHEDIT, False, None, None, None),
            (CRITPATHEDIT, True, None, None, None),
            (NONCRITCREATE, False, False, None, None),
            (NONCRITEDIT, False, False, None, None),
            (EPELCREATE, False, False, None, None),
            (EPELEDIT, False, False, None, None),
            # TLCREATE contains only a 'server'-listed package
            (TLCREATE, False, {'server', 'server-upgrade'}, None, None),
            # TLEDIT contains both 'server' and 'workstation-live-iso'-listed
            # packages
            (TLEDIT, False, {'server', 'server-upgrade', 'workstation-live-iso'}, None, None),
            # TLALLEDIT contains an 'all flavors'-listed package
            (TLALLEDIT, False, None, None, None),
            (RETRIGGER, True, {'server', 'workstation'}, "FEDORA-2021-53a7dfa185", "34"),
            (RETRIGGER, False, False, None, None),
            (NONRETRIGGER, True, None, "FEDORA-2021-53a7dfa185", "34"),
            (NONFRETRIGGER, True, False, None, None),
            (ELNREADY, True, False, None, None),
            (FCOSBUILD, False, None, None, None),
            (FCOSBUILDNOTF, False, False, None, None),
            (FCOSBUILDNOTS, False, False, None, None)
        ]
    )
    def test_scheduler(self, fake_download, fake_fcosbuild, fake_update, fake_schedule, consumer,
                       oqah, message, gotjobs, flavors, advisory, version):
        """Test the job scheduling consumers do their thing. The
        parametrization pairs are:
        1. (consumer, expected openQA hostname)
        2. (fedmsg, job creation? / expected flavors value (see above)
        If jobs are expected, we check the schedule function was hit
        and that the hostname is as expected. If jobs aren't expected,
        we check the schedule function was not hit.
        """
        with mock.patch("openqa_client.client.OpenQA_Client.openqa_request", autospec=True) as fake_request:
            if gotjobs:
                # we mock four existing jobs across two flavors, to
                # make sure we don't duplicate flavors in the request
                fake_request.return_value = {
                    'jobs': [
                        {'id': 1, 'settings': {'FLAVOR': 'updates-server'}, 'state': 'done'},
                        {'id': 2, 'settings': {'FLAVOR': 'updates-server'}, 'state': 'done'},
                        {'id': 3, 'settings': {'FLAVOR': 'updates-workstation'}, 'state': 'done'},
                        {'id': 4, 'settings': {'FLAVOR': 'updates-workstation'}, 'state': 'done'},
                    ]
                }
            else:
                fake_request.return_value = {'jobs': []}
            consumer(message)
        if flavors is False:
            assert fake_schedule.call_count + fake_update.call_count + fake_fcosbuild.call_count == 0
        else:
            archcount = len(consumer.update_arches)
            compcalls = fake_schedule.call_count + fake_fcosbuild.call_count
            updcalls = fake_update.call_count
            # for a compose/fcosbuild test on any consumer, the method
            # should be hit once. for an update test, the method should
            # be hit as many times as the consumer has arches
            # configured
            assert (compcalls == 1 and updcalls == 0) or (compcalls == 0 and updcalls == archcount)
            if fake_schedule.call_count == 1:
                assert fake_schedule.call_args[1]['openqa_hostname'] == oqah
            elif fake_fcosbuild.call_count == 1:
                assert fake_fcosbuild.call_args[1]['openqa_hostname'] == oqah
            else:
                assert fake_update.call_args[1]['openqa_hostname'] == oqah
                assert fake_update.call_args[1]['flavors'] == flavors
                if advisory:
                    assert fake_update.call_args[0][0] == advisory
                if version:
                    assert fake_update.call_args[0][1] == version
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
