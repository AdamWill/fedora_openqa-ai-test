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
# Restarted test message. Note, it really is the case that "id" is an
# int for job.done messages but a str for job.restart messages, check
# real message in datagrepper for verification
RESTARTMSG = Message(
    topic="org.fedoraproject.stg.openqa.job.restart",
    body={
        "ARCH": "x86_64",
        "BUILD": "Fedora-Rawhide-20170207.n.0",
        "FLAVOR": "universal",
        "ISO": "Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
        "MACHINE": "64bit",
        "TEST": "install_asian_language",
        "id": "71262",
        "newbuild": None,
        "remaining": 23,
        "result": {
            "71262": 71264,
            "71263": 71265
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

# Finished incomplete compose message
FINCOMPLETE = Message(
    topic="org.fedoraproject.prod.pungi.compose.status.change",
    body={
        "compose_id": "Fedora-Rawhide-20170206.n.0",
        "location": "http://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170206.n.0/compose",
        "status": "FINISHED_INCOMPLETE"
    }
)

# Bodhi 'update ready for testing' message which is not a re-trigger
# request for a Fedora update
# Edited from
# https://apps.fedoraproject.org/datagrepper/v2/id?id=b89c0a73-8d3d-4783-956e-ca352c9c7317&is_raw=true&size=extra-large
# critpath groups removed to test the codepath that handles messages
# with no critpath groups
# As of Bodhi 8, this is our 'main' scheduling message, we expect to
# see this on update creation, edit-with-changed-builds, and retrigger
NONRETRIGGER = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": False,
        "artifact": {
          "release": "f39",
          "type": "koji-build-group",
          "builds": [
            {
              "component": "annobin",
              "id": 2196428,
              "issuer": "nickc",
              "nvr": "annobin-12.10-2.fc39",
              "scratch": False,
              "task_id": 100764422,
              "type": "koji-build"
            }
          ],
          "repository": "https://bodhi.fedoraproject.org/updates/FEDORA-2023-1f3e17882f",
          "id": "FEDORA-2023-1f3e17882f-498dd481bbc67cb52be72b2b43953ba15443e1d8",
        },
        "contact": {
          "docs": "https://docs.fedoraproject.org/en-US/ci/",
          "team": "Fedora CI",
          "email": "admin@fp.o",
          "name": "Bodhi"
        },
        "version": "0.2.2",
        "agent": "bodhi",
        "generated_at": "2023-05-05T10:53:16.187839Z",
        "update": {
          "alias": "FEDORA-2023-1f3e17882f",
          "critpath": True,
          "release": {
            "branch": "rawhide",
            "dist_tag": "f39",
            "id_prefix": "FEDORA",
            "long_name": "Fedora 39",
            "name": "F39",
            "version": "39"
          }
        }
    }
)

# Non-critpath, non-listed update message
NONCRITCREATE = copy.deepcopy(NONRETRIGGER)
NONCRITCREATE.body['update']['critpath'] = False

# Message with one critpath group, but it's one we schedule no flavors
# for (should result in no jobs)
CPGNFCREATE = copy.deepcopy(NONCRITCREATE)
CPGNFCREATE.body['update']['critpath'] = True
CPGNFCREATE.body['update']['critpath_groups'] = "critical-path-build"

# Non-critpath, one-flavor-listed update message
TLCREATE = copy.deepcopy(NONRETRIGGER)
TLCREATE.body['update']['critpath'] = False
TLCREATE.body['update']['builds'] = [{"epoch": 0, "nvr": "pki-core-10.3.5-11.fc24", "signed": False}]

# Non-critpath, two-flavors-listed update message
TL2CREATE = copy.deepcopy(NONRETRIGGER)
TL2CREATE.body['update']['critpath'] = False
TL2CREATE.body['update']['builds'] = [
    {"epoch": 0, "nvr": "pki-core-10.3.5-11.fc26", "signed": False},
    {"epoch": 0, "nvr": "containernetworking-plugins-4.1.1-3.fc26", "signed": False},
]

# Message with one critpath group, and a package that's in UPDATEDL
# for a *different* flavor
CPTLCREATE = copy.deepcopy(TLCREATE)
CPTLCREATE.body['update']['critpath_groups'] = "critical-path-server"
CPTLCREATE.body['update']['builds'] = [{"epoch": 0, "nvr": "containernetworking-plugins-4.1.1-3.fc26", "signed": False}]

# Critpath EPEL update message
EPELCREATE = copy.deepcopy(NONRETRIGGER)
EPELCREATE.body['update']['release']['id_prefix'] = 'FEDORA-EPEL'

# Message which *is* a re-trigger request. These used to be handled
# differently, we may as well keep the test to make sure we don't
# handle them differently any more
RETRIGGER = copy.deepcopy(NONRETRIGGER)
RETRIGGER.body["re-trigger"] = True
RETRIGGER.body["agent"] = "adamwill"

# Message which is for EPEL stable (should be ignored)
# Based on
# https://apps.fedoraproject.org/datagrepper/v2/id?id=67221afc-de86-4917-a4ac-78dd7bb282e4&is_raw=true&size=extra-large
# but edited to have re-trigger True
NONFRETRIGGER = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": True,
        "artifact": {
          "release": "epel7",
          "type": "koji-build-group",
          "builds": [
            {
              "component": "singularity-ce",
              "id": 2196430,
              "issuer": "dctrud",
              "nvr": "singularity-ce-3.11.3-1.el7",
              "scratch": False,
              "task_id": 100764512,
              "type": "koji-build"
            }
          ],
          "repository": "https://bodhi.fedoraproject.org/updates/FEDORA-EPEL-2023-3b5f9c33da",
          "id": "FEDORA-EPEL-2023-3b5f9c33da-eced24a9de809a343c2c5343c8ae0f80457eee41"
        },
        "contact": {
          "docs": "https://docs.fedoraproject.org/en-US/ci/",
          "team": "Fedora CI",
          "email": "admin@fp.o",
          "name": "Bodhi"
        },
        "version": "0.2.2",
        "agent": "tdawson",
        "generated_at": "2023-05-05T16:15:08.215338Z",
        "update": {
          "alias": "FEDORA-EPEL-2023-3b5f9c33da",
          "critpath": False,
          "critpath_groups": "",
          "release": {
            "branch": "epel7",
            "dist_tag": "epel7",
            "id_prefix": "FEDORA-EPEL",
            "long_name": "Fedora EPEL 7",
            "name": "EPEL-7",
            "version": "7"
          }
        }
    }
)

# Message for ELN, two critpath groups
# based on
# https://apps.fedoraproject.org/datagrepper/v2/id?id=053e4892-eda1-41e8-8f84-7b0c640bc1f6&is_raw=true&size=extra-large
ELNREADY = Message(
    topic="org.fedoraproject.prod.bodhi.update.status.testing.koji-build-group.build.complete",
    body={
        "re-trigger": False,
        "artifact": {
          "type": "koji-build-group",
          "builds": [
            {
              "id": 2541168,
              "nvr": "python-cryptography-43.0.0-3.eln142",
              "task_id": 122953079,
              "type": "koji-build"
            }
          ]
        },
        "agent": "bodhi",
        "update": {
          "alias": "FEDORA-2024-32f9547504",
          "critpath": True,
          "critpath_groups": "critical-path-compose critical-path-server",
          "release": {
            "branch": "eln",
            "dist_tag": "eln",
            "id_prefix": "FEDORA",
            "long_name": "Fedora ELN",
            "name": "ELN",
            "version": "eln"
          }
        }
    }
)

# Like TLCREATE but for ELN - should schedule no jobs as pki-core is
# not in ELNUPDATETL
ELNTLCREATE = copy.deepcopy(ELNREADY)
ELNTLCREATE.body['update']['critpath'] = False
ELNTLCREATE.body['update']['critpath_groups'] = ""
ELNTLCREATE.body['update']['builds'] = [{"epoch": 0, "nvr": "pki-core-10.3.5-11.fc24", "signed": False}]

# Critpath "request testing" message. These are huge, so this is heavily
# edited. Since Bodhi 8, we should *not* trigger on these
CRITPATHRT = Message(
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

# Critpath update edit message (with new/removed builds)
# Since Bodhi 8, we should *not* trigger on these
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
            "builds": [
                {
                    "epoch": 0,
                    "nvr": "codec2-0.6-1.fc24",
                    "signed": False
                },
                {
                    "epoch": 0,
                    "nvr": "freedv-1.2-1.fc24",
                    "signed": False
                }
            ]
        },
        "new_builds": ["codec2-0.6-1.fc24"],
        "removed_builds": ["codec2-0.5-1.fc24"]
    }
)

# Critpath update edit message (without new/removed builds)
# Since Bodhi 8, we should *not* trigger on these
CRITPATHEDITUC = copy.deepcopy(CRITPATHEDIT)
CRITPATHEDITUC.body["new_builds"] = []
CRITPATHEDITUC.body["removed_builds"] = []

# ELN successful compose message. Tests should run
ELNCOMPOSE = Message(
    topic="org.fedoraproject.prod.odcs.compose.state-changed",
    body={
        "compose": {
            "pungi_compose_id": "Fedora-ELN-20230619.1",
            "state": 2,
            "state_name": "done",
            "state_reason": "Compose is generated successfully",
            "toplevel_url": "https://odcs.fedoraproject.org/composes/odcs-28282",
        },
        "event": "state-changed"
    }
)

# ELN compose message which wasn't for a state change
ELNCOMPOSENOTSC = copy.deepcopy(ELNCOMPOSE)
ELNCOMPOSENOTSC.body["event"] = "someotherevent"

# ELN compose message where the state isn't 'done'
ELNCOMPOSENOTDONE = copy.deepcopy(ELNCOMPOSE)
ELNCOMPOSENOTDONE.body["compose"]["state"] = 3

# ODCS compose message which isn't for ELN
ODCSCOMPOSENOTELN = copy.deepcopy(ELNCOMPOSE)
ODCSCOMPOSENOTELN.body["compose"]["pungi_compose_id"] = "odcs-28283-1-20230619.t.0"

# ODCS compose message with the compose ID set to None - this broke
# us in the real world, once
ODCSCOMPOSENOCID = copy.deepcopy(ELNCOMPOSE)
ODCSCOMPOSENOCID.body["compose"]["pungi_compose_id"] = None

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
            # used to affect how re-trigger requests were handled, but
            # no longer does; we now use it to test handling is the same
            # regardless
            # if "advisory" and/or "version" is a string, we'll check
            # that value is used in the update scheduling request. This is
            # for re-trigger request handling, where we do non-trivial
            # parsing to get those values.
            (STARTEDCOMPOSE, False, False, None, None),
            (DOOMEDCOMPOSE, False, False, None, None),
            (FINISHEDCOMPOSE, False, True, None, None),
            (FINCOMPLETE, False, True, None, None),
            # for all critpath updates we should schedule for all flavors
            (NONRETRIGGER, True, None, "FEDORA-2023-1f3e17882f", "39"),
            # not critpath and not listed, so no jobs
            (NONCRITCREATE, False, False, None, None),
            # critpath but group has no associated flavors, so no jobs
            (CPGNFCREATE, False, False, None, None),
            # TLCREATE contains only a 'server'-listed package
            (TLCREATE, False, {'server', 'server-upgrade'}, None, None),
            # TL2CREATE contains both 'server' and 'container'-listed
            # packages
            (TL2CREATE, False, {'server', 'server-upgrade', 'container'}, None, None),
            # CPTLCREATE contains a critpath group package and a
            # package in the TL list for an additional flavor
            (CPTLCREATE, False, {'server', 'server-upgrade', 'container'}, None, None),
            (EPELCREATE, False, False, None, None),
            (RETRIGGER, True, None, "FEDORA-2023-1f3e17882f", "39"),
            (RETRIGGER, False, None, "FEDORA-2023-1f3e17882f", "39"),
            (NONFRETRIGGER, True, False, None, None),
            (ELNREADY, False, False, None, None),
            (ELNTLCREATE, False, False, None, None),
            # we should never schedule for 'request.testing' or 'update.edit'
            # messages since Bodhi 8
            (CRITPATHRT, False, False, None, None),
            (CRITPATHEDIT, False, False, None, None),
            (CRITPATHEDIT, True, False, None, None),
            (CRITPATHEDITUC, False, False, None, None),
            (CRITPATHEDITUC, True, False, None, None),
            (ELNCOMPOSE, True, None, None, None),
            (ELNCOMPOSENOTSC, True, False, None, None),
            (ELNCOMPOSENOTDONE, True, False, None, None),
            (ODCSCOMPOSENOTELN, True, False, None, None),
            (ODCSCOMPOSENOCID, True, False, None, None),
            (FCOSBUILD, False, None, None, None),
            (FCOSBUILDNOTF, False, False, None, None),
            (FCOSBUILDNOTS, False, False, None, None)
        ]
    )
    def test_scheduler(self, fake_fcosbuild, fake_update, fake_schedule, consumer,
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
        """Test we appropriately attempt to report results to
        ResultsDB, with expected default values. Works much the same
        as test_wiki_default; the parametrization tuples specify the
        expected resultsdb_report args for each consumer.
        """
        consumer(PASSMSG)
        assert fake_report.call_count == 1
        assert fake_report.call_args[1]['jobs'] == [71262]
        assert fake_report.call_args[1]['do_report'] == expected['report']
        assert fake_report.call_args[1]['openqa_hostname'] == expected['oqah']
        assert fake_report.call_args[1]['resultsdb_url'] == expected['rdburl']
        fake_report.reset_mock()
        consumer(RESTARTMSG)
        assert fake_report.call_count == 1
        assert fake_report.call_args[1]['jobs'] == [71264,71265]
        assert fake_report.call_args[1]['do_report'] == expected['report']
        assert fake_report.call_args[1]['openqa_hostname'] == expected['oqah']
        assert fake_report.call_args[1]['resultsdb_url'] == expected['rdburl']
        fake_report.reset_mock()

# vim: set textwidth=120 ts=8 et sw=4:
