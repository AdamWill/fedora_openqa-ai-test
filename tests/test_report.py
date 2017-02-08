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

"""Tests for the result reporting code."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
import copy

# external imports
import mock
import openqa_client.client
import pytest
import resultsdb_api
from wikitcms.wiki import ResTuple

# 'internal' imports
from fedora_openqa_schedule.config import CONFIG
import fedora_openqa_schedule.report as fosreport


def test_uniqueres_replacements(jobdict01):
    """Test the _uniqueres_replacements function."""
    basedict = {
        "runarch": "$RUNARCH$",
        "bootmethod": "$BOOTMETHOD$",
        "firmware": "$FIRMWARE$",
        "subvariant": "$SUBVARIANT$",
        "subvariant_or_arm": "$SUBVARIANT_OR_ARM$",
        "imagetype": "$IMAGETYPE$",
        "fs": "$FS$",
        "desktop": "$DESKTOP$",
        "role": "$ROLE$",
    }
    origbase = copy.deepcopy(basedict)
    ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['runarch'] == "x86_64"
    assert ret['bootmethod'] == "x86_64 BIOS"
    assert ret['firmware'] == "BIOS"
    assert ret['subvariant'] == "Server"
    assert ret['subvariant_or_arm'] == "Server"
    assert ret['imagetype'] == "dvd"
    # shouldn't crash, or anything
    assert ret['desktop'] == ''
    assert ret['role'] == ''
    # basedict should not be modified
    assert basedict == origbase

    # sensible value for 'fs' check
    with mock.patch.dict(jobdict01, {'test': 'install_ext3'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['fs'] == 'ext3'

    # sensible value for 'desktop' check
    with mock.patch.dict(jobdict01['settings'], {'DESKTOP': 'gnome'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['desktop'] == 'gnome'

    # sensible value for 'bootmethod' check
    with mock.patch.dict(jobdict01['settings'], {'UEFI': '1'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['bootmethod'] == 'x86_64 UEFI'

    # sensible value for 'role' check
    with mock.patch.dict(jobdict01, {'test': 'role_deploy_domain_controller'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['role'] == 'domain_controller'

    # check Cloud_Base is turned into Cloud for this case
    with mock.patch.dict(jobdict01['settings'], {'SUBVARIANT': 'Cloud_Base'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['subvariant'] == 'Cloud'

    # check ARM stuff
    with mock.patch.dict(jobdict01['settings'], {'ARCH': 'arm'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['subvariant_or_arm'] == 'ARM'
    assert ret['firmware'] == 'ARM'
    assert ret['bootmethod'] == 'ARM'

class TestGetPassedTcNames:
    """Tests for _get_passed_tcnames."""

    def test_list(self, jobdict01):
        """Test the simple list case of _get_passed_tcnames function."""
        # test is server_realmd_join_kickstart
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose')
        assert sorted(ret) == [
            "QA:Testcase_FreeIPA_realmd_login",
            "QA:Testcase_domain_client_authenticate",
            "QA:Testcase_realmd_join_kickstart",
        ]

    def test_deps(self, jobdict01):
        """Test the dict case of _get_passed_tcnames where one test
        suite depends on another.
        """
        jobdict01['test'] = 'desktop_notifications_postinstall'
        # here's a fake openQA client that says the dependent test passed
        fakeclient = mock.create_autospec(openqa_client.client.OpenQA_Client)
        fakeclient.openqa_request.return_value = {
            'jobs': [
                {
                    'test': 'desktop_notifications_live',
                    'result': 'passed',
                }
            ]
        }
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose', fakeclient)
        assert sorted(ret) == [
            "QA:Testcase_desktop_error_checks",
            "QA:Testcase_desktop_update_notification",
        ]

        # now try again with the dependent test failed
        fakeclient.openqa_request.return_value = {
            'jobs': [
                {
                    'test': 'desktop_notifications_live',
                    'result': 'failed',
                }
            ]
        }
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose', fakeclient)
        assert ret == []

        # now try again with the dependent test missing
        fakeclient.openqa_request.return_value = {
            'jobs': [
                {
                    'test': 'someothertest',
                    'result': 'passed',
                }
            ]
        }
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose', fakeclient)
        assert ret == []

    def test_modules(self, jobdict01):
        """Test the dict case of _get_passed_tcnames where test modules
        must be passed.
        """
        jobdict01['test'] = 'realmd_join_cockpit'
        # say one of the required modules passed, one failed
        jobdict01['modules'] = [
            {
                'name': 'freeipa_webui',
                'result': 'passed',
            },
            {
                'name': 'freeipa_password_change',
                'result': 'failed',
            },
        ]
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose')
        assert sorted(ret) == [
            "QA:Testcase_FreeIPA_realmd_login",
            "QA:Testcase_FreeIPA_web_ui",
            "QA:Testcase_domain_client_authenticate",
            "QA:Testcase_realmd_join_cockpit",
        ]

    def test_module_missing(self, jobdict01):
        """Test the dict case of _get_passed_tcnames where test modules
        must be passed, if the module cannot be found in the result.
        """
        jobdict01['test'] = 'realmd_join_cockpit'
        # no modules! what!
        jobdict01['modules'] = []
        # shouldn't crash or do anything weird, just not report the
        # module dependent tests as passed
        ret = fosreport._get_passed_tcnames(jobdict01, 'somecompose')
        assert sorted(ret) == [
            "QA:Testcase_FreeIPA_realmd_login",
            "QA:Testcase_domain_client_authenticate",
            "QA:Testcase_realmd_join_cockpit",
        ]

    def test_error(self):
        """Check _get_passed_tcnames returns if testcase name isn't in
        TESTSUITES.
        """
        ret = fosreport._get_passed_tcnames({'test': 'nonexistenttest'}, 'somecompose')
        assert ret == []


class TestGetPassedTestcases:
    """Tests for get_passed_testcases."""

    def test_simple(self, jobdict01):
        """Test the simple get_passed_testcases case where the job did
        pass.
        """
        ret = fosreport.get_passed_testcases([jobdict01])
        # function is supposed to sort for us
        assert len(ret) == 3
        assert ret[0] == ResTuple(
            testtype='Server',
            release='',
            milestone='',
            compose='',
            testcase='QA:Testcase_FreeIPA_realmd_login',
            section=None,
            testname='',
            env='Result',
            status='pass',
            user='',
            bugs='',
            comment='',
            bot=True,
            cid='Fedora-Rawhide-20170207.n.0'
        )
        assert ret[1] == ResTuple(
            testtype='Server',
            release='',
            milestone='',
            compose='',
            testcase='QA:Testcase_domain_client_authenticate',
            section=None,
            testname='(FreeIPA)',
            env='Result',
            status='pass',
            user='',
            bugs='',
            comment='',
            bot=True,
            cid='Fedora-Rawhide-20170207.n.0'
        )
        assert ret[2] == ResTuple(
            testtype='Server',
            release='',
            milestone='',
            compose='',
            testcase='QA:Testcase_realmd_join_kickstart',
            section='FreeIPA',
            testname='',
            env='Result',
            status='pass',
            user='',
            bugs='',
            comment='',
            bot=True,
            cid='Fedora-Rawhide-20170207.n.0'
        )

    def test_fail(self, jobdict01):
        """Check get_passed_testcases returns nothing when job failed."""
        jobdict01['result'] = 'failed'
        ret = fosreport.get_passed_testcases([jobdict01])
        assert len(ret) == 0

    @mock.patch('fedora_openqa_schedule.report._get_passed_tcnames', return_value=['unknowntestcase'])
    def test_missing(self, faketcnames, jobdict01):
        """Check get_passed_testcases returns nothing (but doesn't crash)
        when testcase isn't in TESTCASES.
        """
        ret = fosreport.get_passed_testcases([jobdict01])
        assert len(ret) == 0

    def test_extra(self, jobdict01):
        """Check get_passed_testcases returns nothing when build ends in
        EXTRA (indicating a modified test run).
        """
        jobdict01['settings']['BUILD'] = 'Fedora-Rawhide-20170207.n.0-EXTRA'
        ret = fosreport.get_passed_testcases([jobdict01])
        assert len(ret) == 0


@mock.patch('fedora_openqa_schedule.report.get_passed_testcases', return_value=['atest'], autospec=True)
@pytest.mark.usefixtures("oqaclientmock")
class TestWikiReport:
    """Tests for the wiki_report function."""

    def test_default(self, fake_getpassed, wikimock):
        """Check default case behaviour behaviour."""
        # mockclass is the MagicMock for the *class itself*; we use it to
        # check the args passed when instantiating the class. mockinst is
        # the MagicMock that's always returned when instantiating the
        # class, the mock 'instance' of Wiki we're working with.
        (mockclass, mockinst) = wikimock
        fosreport.wiki_report(jobs=[1])
        # check we respected config default hostname
        assert mockclass.call_args[0][0][1] == CONFIG.get('report', 'wiki_hostname')
        # check our fake get_passed_testcases result was passed to
        # report_validation_results
        assert mockinst.report_validation_results.call_args[0][0] == ['atest']

    def test_wiki_hostname(self, fake_getpassed, wikimock):
        """Check wiki hostname is passed through."""
        (mockclass, mockinst) = wikimock
        fosreport.wiki_report(wiki_hostname='foo.bar', jobs=[1])
        assert mockclass.call_args[0][0][1] == 'foo.bar'
        # check results still happened
        assert mockinst.report_validation_results.call_args[0][0] == ['atest']

    def test_oqa_hostname(self, fake_getpassed, wikimock, oqaclientmock):
        """Check openQA hostname is passed through."""
        (_, mockinst) = wikimock
        fosreport.wiki_report(openqa_hostname='foo.bar', jobs=[1])
        # similarly to mockclass note, this is the MagicMock of the
        # OpenQA_Client class itself, we use it to check the instantiation
        # args.
        mockoqaclass = oqaclientmock[0]
        assert mockoqaclass.call_args[0][0] == 'foo.bar'
        # check results still happened
        assert mockinst.report_validation_results.call_args[0][0] == ['atest']

    def test_do_report(self, fake_getpassed, wikimock):
        """Check do_report=False disables reporting."""
        (_, mockinst) = wikimock
        # check do_report works
        fosreport.wiki_report(jobs=[1], do_report=False)
        # check results didn't happen
        assert mockinst.report_validation_results.call_args is None


@mock.patch.object(resultsdb_api.ResultsDBapi, 'create_result')
@pytest.mark.usefixtures("ffmock", "oqaclientmock")
class TestResultsDBReport:
    """Tests for the resultsdb_report function."""

    def test_simple(self, fakeres, jobdict01):
        """Check resultsdb_report behaviour with our stock fake data."""
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso'
        assert fakeres.call_args[1]['ref_url'] == 'https://some.url/tests/70581'
        assert fakeres.call_args[1]['testcase']['name'] == 'compose.server_realmd_join_kickstart'
        assert fakeres.call_args[1]['firmware'] == 'bios'
        assert fakeres.call_args[1]['outcome'] == 'PASSED'

    def test_uefi(self, fakeres, oqaclientmock):
        """Check resultsdb_report with UEFI test."""
        # modify the job dict used by the mock fixture
        jobdict = oqaclientmock[2]
        jobdict['settings']['UEFI'] = '1'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['firmware'] == 'uefi'

    def test_outcome(self, fakeres, oqaclientmock):
        "Check resultsdb_report outcome."""
        jobdict = oqaclientmock[2]
        jobdict['result'] = 'failed'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['outcome'] == 'FAILED'

        fakeres.reset_mock()
        jobdict['result'] = 'parallel_failed'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['outcome'] == 'FAILED'

        jobdict['result'] = 'softfailed'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['outcome'] == 'INFO'

        jobdict['result'] = 'cancelled'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['outcome'] == 'NEEDS_INSPECTION'

    def test_test_target(self, fakeres, ffmock, oqaclientmock):
        """Check resultsdb_report TEST_TARGET behaviour."""
        jobdict = oqaclientmock[2]
        imgdict = ffmock[1]
        mods = {'TEST_TARGET': 'HDD_1', 'HDD_1': 'somefile.img'}
        with mock.patch.dict(jobdict['settings'], mods):
            with mock.patch.dict(imgdict, {'path': '/path/to/somefile.img'}):
                fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'somefile.img'

        jobdict['settings']['TEST_TARGET'] = 'COMPOSE'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'Fedora-Rawhide-20170207.n.0'

        fakeres.reset_mock()
        jobdict['settings']['TEST_TARGET'] = 'NONE'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['settings']['TEST_TARGET'] = 'foo'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['settings']['TEST_TARGET'] = ''
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        del jobdict['settings']['TEST_TARGET']
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

    def test_skips(self, fakeres, oqaclientmock):
        """Check resultsdb_report skips reporting for cloned,
        cancelled, obsolete and incomplete jobs.
        """
        jobdict = oqaclientmock[2]
        with mock.patch.dict(jobdict, {'clone_id': 15}):
            fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['result'] = 'user_cancelled'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['result'] = 'obsoleted'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        jobdict['result'] = 'passed'
        for required in ('BUILD', 'DISTRI', 'VERSION'):
            fakeres.reset_mock()
            backup = jobdict['settings'][required]
            del jobdict['settings'][required]
            fosreport.resultsdb_report(jobs=[1])
            assert fakeres.call_count == 0
            jobdict['settings'][required] = backup

    def test_note(self, fakeres, oqaclientmock):
        """Check resultsdb_report adds a note for failed modules."""
        jobdict = oqaclientmock[2]
        mods = {
            'result': 'failed',
            'modules': [
                {
                    "category": "tests",
                    "flags": ["fatal"],
                    "name": "_boot_to_anaconda",
                    "result": "failed"
                },
            ]
        }
        with mock.patch.dict(jobdict, mods):
            fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['note'] == '_boot_to_anaconda module failed'

        fakeres.reset_mock()
        mods = {
            'result': 'softfailed',
            'modules': [
                {
                    "category": "tests",
                    "flags": [],
                    "name": "_boot_to_anaconda",
                    "result": "failed"
                },
                {
                    "category": "tests",
                    "flags": [],
                    "name": "_next_step",
                    "result": "failed"
                },
            ]
        }
        with mock.patch.dict(jobdict, mods):
            fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['note'] == 'non-important module _next_step failed'

# vim: set textwidth=120 ts=8 et sw=4:
