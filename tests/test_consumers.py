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

# external imports
import mock
import pytest

# 'internal' imports
import fedora_openqa.consumer

# Passed test message
PASSMSG = {
    'body': {
        "i": 1,
        "msg": {
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
        },
        "msg_id": "2017-0c3079cf-b21c-4aca-89b1-982d37ce4065",
        "source_name": "datanommer",
        "source_version": "0.6.5",
        "timestamp": 1486473322.0,
        "topic": "org.fedoraproject.stg.openqa.job.done"
    }
}

# Started compose message
STARTEDCOMPOSE = {
    'body': {
        "i": 1,
        "msg": {
            "compose_id": "Fedora-Atomic-25-20170206.0",
            "location": "http://kojipkgs.fedoraproject.org/compose/twoweek/Fedora-Atomic-25-20170206.0/compose",
            "status": "STARTED"
        },
        "msg_id": "2017-e6670216-2f1a-45d8-b338-3e6da221c467",
        "source_name": "datanommer",
        "source_version": "0.6.5",
        "timestamp": 1486358122.0,
        "topic": "org.fedoraproject.prod.pungi.compose.status.change"
    }
}

# Doomed compose message
DOOMEDCOMPOSE = {
    'body': {
        "i": 1,
        "msg": {
            "compose_id": "Fedora-Docker-25-20170206.0",
            "location": "http://kojipkgs.fedoraproject.org/compose/Fedora-Docker-25-20170206.0/compose",
            "status": "DOOMED"
        },
        "msg_id": "2017-984d8234-a6be-4df4-937d-cb778d4e689f",
        "source_name": "datanommer",
        "source_version": "0.6.5",
        "timestamp": 1486360017.0,
        "topic": "org.fedoraproject.prod.pungi.compose.status.change"
    }
}

# Finished compose message
FINISHEDCOMPOSE = {
    'body': {
        "i": 1,
        "msg": {
            "compose_id": "Fedora-Atomic-25-20170206.0",
            "location": "http://kojipkgs.fedoraproject.org/compose/twoweek/Fedora-Atomic-25-20170206.0/compose",
            "status": "FINISHED"
        },
        "msg_id": "2017-6fedef19-1f2c-44ff-bef5-f59b69eaa0c0",
        "source_name": "datanommer",
        "source_version": "0.6.5",
        "timestamp": 1486363419.0,
        "topic": "org.fedoraproject.prod.pungi.compose.status.change"
    }
}

# Finished incomplete compose message
FINCOMPLETE = {
    'body': {
        "i": 1,
        "msg": {
            "compose_id": "Fedora-Rawhide-20170206.n.0",
            "location": "http://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170206.n.0/compose",
            "status": "FINISHED_INCOMPLETE"
        },
        "msg_id": "2017-a396bf9d-48be-477e-a07c-bf69daf044ca",
        "source_name": "datanommer",
        "source_version": "0.6.5",
        "timestamp": 1486378978.0,
        "topic": "org.fedoraproject.prod.pungi.compose.status.change"
    }
}

# proper consumer init requires a fedmsg hub instance, we don't have
# one and don't want to faff around faking one.
with mock.patch('fedmsg.consumers.FedmsgConsumer.__init__', return_value=None):
    PRODSCHED = fedora_openqa.consumer.OpenQAProductionScheduler(None)
    STGSCHED = fedora_openqa.consumer.OpenQAStagingScheduler(None)
    TESTSCHED = fedora_openqa.consumer.OpenQATestScheduler(None)
    PRODWIKI = fedora_openqa.consumer.OpenQAProductionWikiReporter(None)
    STGWIKI = fedora_openqa.consumer.OpenQAStagingWikiReporter(None)
    TESTWIKI = fedora_openqa.consumer.OpenQATestWikiReporter(None)
    PRODRDB = fedora_openqa.consumer.OpenQAProductionResultsDBReporter(None)
    STGRDB = fedora_openqa.consumer.OpenQAStagingResultsDBReporter(None)
    TESTRDB = fedora_openqa.consumer.OpenQATestResultsDBReporter(None)

PRODS = (PRODWIKI, PRODRDB, PRODSCHED)
STGS = (STGWIKI, STGRDB, STGSCHED)
# we don't include TESTSCHED as its values are hardcoded
TESTS = (TESTWIKI, TESTRDB)

for _con in PRODS + STGS + TESTS + (TESTSCHED,):
    # skipping __init__ means this doesn't get set up, so mock it
    _con.log = mock.Mock()

@pytest.mark.usefixtures("ffmock")
class TestConsumers:
    """Tests for the consumers."""

    @mock.patch('fedora_openqa.schedule.jobs_from_compose', return_value=('somecompose', [1]), autospec=True)
    @pytest.mark.parametrize(
        "consumer,oqah",
        [
            (PRODSCHED, 'openqa.fedoraproject.org'),
            (STGSCHED, 'openqa.stg.fedoraproject.org'),
            (TESTSCHED, 'localhost'),
        ]
    )
    @pytest.mark.parametrize(
        "message,create",
        [
            (STARTEDCOMPOSE, False),
            (DOOMEDCOMPOSE, False),
            (FINISHEDCOMPOSE, True),
            (FINCOMPLETE, True),
        ]
    )
    def test_scheduler(self, fake_schedule, consumer, oqah, message, create):
        """Test the job scheduling consumers do their thing. The
        parametrization pairs are:
        1. (consumer, expected openQA hostname)
        2. (fedmsg, should job scheduling happen?)
        If jobs are expected, we check the schedule function was hit
        and that the hostname is as expected. If jobs aren't expected,
        we check the schedule function was not hit.
        """
        consumer.consume(message)
        if create:
            assert fake_schedule.call_count == 1
            assert fake_schedule.call_args[1]['openqa_hostname'] == oqah
        else:
            assert fake_schedule.call_count == 0
        fake_schedule.reset_mock()


    @mock.patch('fedora_openqa.report.wiki_report', autospec=True)
    @pytest.mark.parametrize(
        "consumer,expected",
        [
            (PRODWIKI, {'report': False, 'oqah': 'openqa.fedoraproject.org', 'wikih': 'fedoraproject.org'}),
            (STGWIKI, {'report': False, 'oqah': 'openqa.stg.fedoraproject.org', 'wikih': 'stg.fedoraproject.org'}),
            (TESTWIKI, {'report': False, 'oqah': 'openqa.fedoraproject.org', 'wikih': 'stg.fedoraproject.org'}),
        ]
    )
    def test_wiki_default(self, fake_report, consumer, expected):
        """Test we appropriately attempt to report results for a passed
        test to the wiki, with expected default values, for each wiki
        consumer. The parametrization tuples specify the expected args
        to the wiki_report call for each consumer. We compare against
        the call_args of the mock.
        """
        consumer.consume(PASSMSG)
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
                    'report': False,
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
                    'report': True,
                    'oqah': 'openqa.fedoraproject.org',
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
        consumer.consume(PASSMSG)
        assert fake_report.call_count == 1
        assert fake_report.call_args[1]['jobs'] == [71262]
        assert fake_report.call_args[1]['do_report'] == expected['report']
        assert fake_report.call_args[1]['openqa_hostname'] == expected['oqah']
        assert fake_report.call_args[1]['resultsdb_url'] == expected['rdburl']
        fake_report.reset_mock()


    @mock.patch('fedora_openqa.schedule.jobs_from_compose', return_value=('somecompose', []), autospec=True)
    @mock.patch('fedora_openqa.report.resultsdb_report', autospec=True)
    @mock.patch('fedora_openqa.report.wiki_report', autospec=True)
    @pytest.mark.parametrize(
        "consumers,setting,value,arg,expected",
        [
            (PRODS, 'prod_oqa_hostname', 'testing', 'openqa_hostname', 'testing'),
            (STGS, 'stg_oqa_hostname', 'testing', 'openqa_hostname', 'testing'),
            (TESTS, 'test_oqa_hostname', 'testing', 'openqa_hostname', 'testing'),
            # openqa_baseurl isn't used or passed by the schedulers
            ([PRODWIKI, PRODRDB], 'prod_oqa_baseurl', 'https://test.ing', 'openqa_baseurl', 'https://test.ing'),
            ([STGWIKI, STGRDB], 'stg_oqa_baseurl', 'https://test.ing', 'openqa_baseurl', 'https://test.ing'),
            (TESTS, 'test_oqa_baseurl', 'https://test.ing', 'openqa_baseurl', 'https://test.ing'),
            ([PRODWIKI], 'prod_wiki_hostname', 'testing', 'wiki_hostname', 'testing'),
            ([STGWIKI], 'stg_wiki_hostname', 'testing', 'wiki_hostname', 'testing'),
            ([TESTWIKI], 'test_wiki_hostname', 'testing', 'wiki_hostname', 'testing'),
            ([PRODWIKI], 'prod_wiki_report', 'true', 'do_report', True),
            ([STGWIKI], 'stg_wiki_report', 'true', 'do_report', True),
            ([TESTWIKI], 'test_wiki_report', 'true', 'do_report', True),
            ([PRODRDB], 'prod_rdb_url', 'https://test.ing', 'resultsdb_url', 'https://test.ing'),
            ([STGRDB], 'stg_rdb_url', 'https://test.ing', 'resultsdb_url', 'https://test.ing'),
            ([TESTRDB], 'test_rdb_url', 'https://test.ing', 'resultsdb_url', 'https://test.ing'),
            ([PRODRDB], 'prod_rdb_report', 'true', 'do_report', True),
            ([STGRDB], 'stg_rdb_report', 'true', 'do_report', True),
            ([TESTRDB], 'test_rdb_report', 'true', 'do_report', True),
        ]
    )
    def test_configs(self, fake_wiki, fake_rdb, fake_sched, consumers, setting, value, arg, expected):
        """Test configuration settings are properly respected by all
        consumers. The parametrization tuples specify an iterable of
        consumers, a config setting name in the 'consumers' section,
        the value to which it should be set, the name of the arg whose
        value should be affected by the setting, and the value the arg
        should get. We mock all three of the functions that the three
        different consumers call, and each time, we just find the one
        whose call_count is 1 to know which one got hit, then we check
        the arg.
        """
        backup = fedora_openqa.consumer.CONFIG.get('consumers', setting)
        fedora_openqa.consumer.CONFIG.set('consumers', setting, value)
        for consumer in consumers:
            for fake in (fake_wiki, fake_rdb, fake_sched):
                fake.reset_mock()
            if isinstance(consumer, fedora_openqa.consumer.OpenQAScheduler):
                consumer.consume(FINISHEDCOMPOSE)
            else:
                consumer.consume(PASSMSG)
            # figure out which mock to check the calls for
            fake = next(fake for fake in (fake_wiki, fake_rdb, fake_sched) if fake.call_count == 1)
            assert fake.call_args[1][arg] == expected
        fedora_openqa.consumer.CONFIG.set('consumers', setting, backup)

# vim: set textwidth=120 ts=8 et sw=4:
