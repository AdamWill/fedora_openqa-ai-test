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
from unittest import mock

# external imports
import openqa_client.client
import pytest
import resultsdb_api
from wikitcms.wiki import ResTuple

# 'internal' imports
from fedora_openqa.config import CONFIG
import fedora_openqa.report as fosreport


def test_uniqueres_replacements(jobdict01):
    """Test the _uniqueres_replacements function."""
    basedict = {
        "runarch": "$RUNARCH$",
        "bootmethod": "$BOOTMETHOD$",
        "firmware": "$FIRMWARE$",
        "subvariant": "$SUBVARIANT$",
        "imagetype": "$IMAGETYPE$",
        "fs": "$FS$",
        "desktop": "$DESKTOP$",
    }
    origbase = copy.deepcopy(basedict)
    ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['runarch'] == "x86_64"
    assert ret['bootmethod'] == "x86_64 BIOS"
    assert ret['firmware'] == "BIOS"
    assert ret['subvariant'] == "Server"
    assert ret['imagetype'] == "dvd"
    # shouldn't crash, or anything
    assert ret['desktop'] == ''
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

    # check Cloud_Base is turned into Cloud for this case
    with mock.patch.dict(jobdict01['settings'], {'SUBVARIANT': 'Cloud_Base'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['subvariant'] == 'Cloud'

    # check ARM stuff
    with mock.patch.dict(jobdict01['settings'], {'ARCH': 'arm'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['firmware'] == 'ARM'
    assert ret['bootmethod'] == 'ARM'

    # and aarch64
    with mock.patch.dict(jobdict01['settings'], {'ARCH': 'aarch64'}):
        ret = fosreport._uniqueres_replacements(jobdict01, basedict)
    assert ret['firmware'] == 'UEFI'
    assert ret['bootmethod'] == 'aarch64'

class TestGetPassedTcNames:
    """Tests for _get_passed_tcnames."""

    def test_list(self, jobdict01):
        """Test the simple list case of _get_passed_tcnames function."""
        # test is server_realmd_join_kickstart
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose')
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
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose', fakeclient)
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
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose', fakeclient)
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
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose', fakeclient)
        assert ret == []

    def test_modules(self, jobdict01):
        """Test the dict case of _get_passed_tcnames where test modules
        must be passed. We test behaviour both with overall job result
        'passed' (where the passed module test case and the test cases
        related to the overall job result should be returned) and with
        overall job result 'failed' (where only the passed module test
        case should be returned).
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
        # with overall job result 'passed'...
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose')
        assert sorted(ret) == [
            "QA:Testcase_FreeIPA_realmd_login",
            "QA:Testcase_FreeIPA_web_ui",
            "QA:Testcase_domain_client_authenticate",
            "QA:Testcase_realmd_join_cockpit",
        ]
        # now with overall job result 'failed'
        ret = fosreport._get_passed_tcnames(jobdict01, 'failed', 'somecompose')
        assert sorted(ret) == [
            # only the case that has a module conditional
            "QA:Testcase_FreeIPA_web_ui",
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
        ret = fosreport._get_passed_tcnames(jobdict01, 'passed', 'somecompose')
        assert sorted(ret) == [
            "QA:Testcase_FreeIPA_realmd_login",
            "QA:Testcase_domain_client_authenticate",
            "QA:Testcase_realmd_join_cockpit",
        ]

    def test_error(self):
        """Check _get_passed_tcnames returns if testcase name isn't in
        TESTSUITES.
        """
        ret = fosreport._get_passed_tcnames({'test': 'nonexistenttest'}, 'passed', 'somecompose')
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

    def test_iot(self, jobdict03):
        """Check get_passed_testcases works correctly for a result
        from an IoT compose.
        """
        ret = fosreport.get_passed_testcases([jobdict03])
        assert len(ret) == 1
        assert ret[0] == ResTuple(
            testtype="General",
            release="",
            milestone="",
            compose="",
            testcase="QA:Testcase_base_selinux",
            section="",
            testname="",
            env="x86_64",
            status="pass",
            user="",
            bugs="",
            comment="",
            bot=True,
            cid="Fedora-IoT-33-20200513.0"
        )

    def test_fail(self, jobdict01):
        """Check get_passed_testcases returns nothing when job failed."""
        jobdict01['result'] = 'failed'
        ret = fosreport.get_passed_testcases([jobdict01])
        assert len(ret) == 0

    @mock.patch('fedora_openqa.report._get_passed_tcnames', return_value=['unknowntestcase'])
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

    def test_noreport(self, jobdict01):
        """Check get_passed_testcases returns nothing when build ends in
        NOREPORT (intended for use by admins when manually triggering some
        kind of 'throwaway' test run).
        """
        jobdict01['settings']['BUILD'] = 'Fedora-Rawhide-20170207.n.0-NOREPORT'
        ret = fosreport.get_passed_testcases([jobdict01])
        assert len(ret) == 0


@mock.patch('fedora_openqa.report.get_passed_testcases', return_value=['atest'], autospec=True)
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
        assert mockclass.call_args[0][0] == CONFIG.get('report', 'wiki_hostname')
        # check our fake get_passed_testcases result was passed to
        # report_validation_results
        assert mockinst.report_validation_results.call_args[0][0] == ['atest']

    def test_wiki_hostname(self, fake_getpassed, wikimock):
        """Check wiki hostname is passed through."""
        (mockclass, mockinst) = wikimock
        fosreport.wiki_report(wiki_hostname='foo.bar', jobs=[1])
        assert mockclass.call_args[0][0] == 'foo.bar'
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

    def test_update_noreport(self, fake_getpassed, wikimock, oqaclientmock, jobdict02):
        """Check we do no reporting (but don't crash or do anything
        else odd) for an update test job.
        """
        # adjust the OpenQA_Client instance mock to return jobdict02
        instmock = oqaclientmock[1]
        instmock.get_jobs.return_value = [jobdict02]
        (_, mockinst) = wikimock
        ret = fosreport.wiki_report(jobs=[1])
        # check results didn't happen
        assert mockinst.report_validation_results.call_args is None
        assert ret == []

    def test_coreos_noreport(self, fake_getpassed, wikimock, oqaclientmock, jobdict04):
        """Check we do no reporting for Fedora CoreOS jobs."""
        # adjust the OpenQA_Client instance mock to return jobdict04
        instmock = oqaclientmock[1]
        instmock.get_jobs.return_value = [jobdict04]
        (_, mockinst) = wikimock
        ret = fosreport.wiki_report(jobs=[1])
        # check results didn't happen
        assert mockinst.report_validation_results.call_args is None
        assert ret == []

    def test_no_jobs_noreport(self, fake_getpassed, wikimock, oqaclientmock):
        """Check we do no reporting if we find no jobs."""
        # adjust the OpenQA_Client instance mock to return nothing
        instmock = oqaclientmock[1]
        instmock.get_jobs.return_value = []
        (_, mockinst) = wikimock
        ret = fosreport.wiki_report(jobs=[1])
        # check results didn't happen
        assert mockinst.report_validation_results.call_args is None
        assert ret == []


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
        scenario = 'fedora.Server-dvd-iso.x86_64.64bit'
        assert fakeres.call_args[1]['scenario'] == scenario

    def test_update(self, fakeres, oqaclientmock, jobdict02):
        """Check report behaviour with an update test job (rather than
        a compose test job).
        """
        # adjust the OpenQA_Client instance mock to return jobdict02
        instmock = oqaclientmock[1]
        instmock.get_jobs.return_value = [jobdict02]
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'FEDORA-2017-376ae2b92c'
        assert fakeres.call_args[1]['ref_url'] == 'https://some.url/tests/72517'
        assert fakeres.call_args[1]['testcase']['name'] == 'update.base_selinux'
        assert fakeres.call_args[1]['firmware'] == 'bios'
        assert fakeres.call_args[1]['outcome'] == 'PASSED'

    def test_coreos(self, fakeres, oqaclientmock, jobdict04):
        """Check resultsdb_report behaviour with a CoreOS job."""
        # adjust the OpenQA_Client instance mock to return jobdict04
        instmock = oqaclientmock[1]
        instmock.get_jobs.return_value = [jobdict04]
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == "fedora-coreos-32.20200726.3.1-live.x86_64.iso"
        assert fakeres.call_args[1]['ref_url'] == "https://some.url/tests/48192"
        assert fakeres.call_args[1]['testcase']['name'] == "fcosbuild.base_services_start"
        assert fakeres.call_args[1]['firmware'] == "bios"
        assert fakeres.call_args[1]['outcome'] == "PASSED"

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

        # our ARM tests have the decompressed filename as HDD_1, but
        # we need to pass the compressed filename to rdb_conventions,
        # there is special code to handle this: check it
        mods = {'TEST_TARGET': 'HDD_1', 'HDD_1': 'somefile.raw', 'IMAGETYPE': 'raw-xz'}
        with mock.patch.dict(jobdict['settings'], mods):
            with mock.patch.dict(imgdict, {'path': '/path/to/somefile.raw.xz'}):
                fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'somefile.raw.xz'

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
        cancelled, obsolete, incomplete, EXTRA, NOREPORT and Koji task
        jobs.
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

        fakeres.reset_mock()
        jobdict['settings']['BUILD'] = 'Fedora-Rawhide-20170207.n.0-EXTRA'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['settings']['BUILD'] = 'Fedora-Rawhide-20170207.n.0-NOREPORT'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

        fakeres.reset_mock()
        jobdict['settings']['BUILD'] = 'Fedora-Rawhide-20170207.n.0'
        jobdict['settings']['KOJITASK'] = '32099714'
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_count == 0

    def test_updates_testing(self, fakeres, oqaclientmock):
        """Check we strip the 'testing-' that we add to the asset file
        name for updates-testing images before reporting results.
        """
        jobdict = oqaclientmock[2]
        with mock.patch.dict(jobdict['settings'], {'ISO': 'testing-Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso'}):
            fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso'

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

    @mock.patch("time.sleep", autospec=True)
    def test_retries(self, fakesleep, fakeres, jobdict01):
        """Test the retry handling stuff."""
        # if we always hit an error, we should eventually raise it
        fakeres.side_effect = ValueError("foo")
        with pytest.raises(ValueError) as err:
            fosreport.resultsdb_report(jobs=[1])
            assert isinstance(err, ValueError)
            assert str(err) == "foo"
        # if the error only happens a few times, we should retry and
        # get past it
        fakeres.side_effect = [ValueError("foo"), ValueError("bar"), None]
        fosreport.resultsdb_report(jobs=[1])
        assert fakeres.call_args[1]['item'] == 'Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso'

# vim: set textwidth=120 ts=8 et sw=4:
