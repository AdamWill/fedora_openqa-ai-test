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
# pylint: disable=old-style-class, no-init, protected-access, no-self-use, unused-argument, too-many-arguments

"""Tests for the CLI code."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
import copy
from unittest import mock

# external imports
from freezegun import freeze_time
import pytest

# 'internal' imports
import fedora_openqa.cli as cli

UPDATEJSON = {
    'update': {
        'builds': [
            {
                'nvr': 'cockpit-129-1.fc25',
                'release_id': 15,
                'signed': True,
                'type': 'rpm',
                'epoch': 0
            },
        ],
        'release': {
            'version': '25'
        }
    }
}


@mock.patch('fedora_openqa.schedule.jobs_from_compose', return_value=[None, (1, 2)], autospec=True)
class TestCommandCompose:
    """Tests for the command_compose function."""

    def test_simple(self, fakejfc, capsys):
        """Test with simplest invocation."""
        args = cli.parse_args(
            ['compose', 'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose']
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        (out, _) = capsys.readouterr()
        # should print out list of scheduled jobs
        assert out == "Scheduled jobs: 1, 2\n"
        # should exit 0
        assert not excinfo.value.code
        # shouldn't force
        assert fakejfc.call_args[1]['force'] is False
        # should pass arches as 'None'
        assert fakejfc.call_args[1]['arches'] is None
        # should pass flavors as 'None'
        assert fakejfc.call_args[1]['flavors'] is None

    def test_force(self, fakejfc):
        """Test with -f (force)."""
        args = cli.parse_args(
            ['compose', 'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose', '-f']
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        # should exit 0
        assert not excinfo.value.code
        # should force
        assert fakejfc.call_args[1]['force'] is True

    def test_updates(self, fakejfc):
        """Test with --updates."""
        args = cli.parse_args([
            'compose',
            'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose',
            '--updates=https://www.foo.com/updates.img'
        ])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        # should exit 0
        assert not excinfo.value.code
        # should add extra params
        assert fakejfc.call_args[1]['extraparams'] == {'GRUBADD': "inst.updates=https://www.foo.com/updates.img"}

    @pytest.mark.parametrize(
        ("arg", "values"),
        [
            ('arches', ('x86_64', 'ppc64le,aarch64')),
            ('flavors', ('server-boot-iso', 'workstation-live-iso,universal')),
        ]
    )
    def test_arches_flavors(self, fakejfc, arg, values):
        """Test with --arches and --flavors, using parametrization.
        'arg' is the argument name. 'values' is a tuple of two value
        strings, the first a single appropriate value for the arg, the
        second a comma-separated list of two appropriate values.
        """
        args = cli.parse_args([
            'compose',
            'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose',
            '--{0}={1}'.format(arg, values[0])
        ])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        # should exit 0
        assert not excinfo.value.code
        # should specify arch/flavor as single-item list
        assert fakejfc.call_args[1][arg] == [values[0]]
        args = cli.parse_args([
            'compose',
            'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose',
            '--{0}={1}'.format(arg, values[1])
        ])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        # should exit 0
        assert not excinfo.value.code
        # should specify arches/flavors as multi-item list
        assert fakejfc.call_args[1][arg] == values[1].split(',')

    def test_nojobs(self, fakejfc):
        """Test exits 1 when no jobs are run."""
        # adjust mock return value to say no jobs run
        fakejfc.return_value = [None, []]
        args = cli.parse_args(
            ['compose', 'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose']
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_compose(args)
        # should exit 1
        assert excinfo.value.code == 1


class TestCommandUpdateTask:
    """Tests for the command_update_task function."""
    @pytest.mark.parametrize(
        "target",
        # update ID, task ID or tag (to test all paths)
        ['FEDORA-2017-b07d628952', '32099714', '32099714,32099715', 'f39-python', 'foo/somecopr']
    )
    @mock.patch('fedfind.helpers.download_json', return_value=UPDATEJSON, autospec=True)
    @mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1, 2], autospec=True)
    def test_command_update_task(self, fakejfu, fakejson, target, capsys):
        """General tests for the command_update_task function."""
        if target.replace(",", "0").isdigit():
            testargs = ('task', target, '25')
            # we parse the target a bit for tasks
            target = target.split(",")
        elif target.startswith("FEDORA"):
            testargs = ('update', '--release', '25', target)
        elif target.startswith("f39"):
            testargs = ('tag', target, '25')
            # we munge the target a bit for tags
            target = "TAG_" + target
        elif target.startswith("foo"):
            testargs = ('copr', target, '25')
            # we munge the target a bit for COPRs
            target = "COPR_" + target
        args = cli.parse_args(testargs)
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        (out, _) = capsys.readouterr()
        # first arg should be target
        assert fakejfu.call_args[0][0] == target
        # second should be release
        assert fakejfu.call_args[1]['version'] == 25
        # flavors kwarg should be false-y (not, e.g., [None])
        assert not fakejfu.call_args[1]['flavors']
        # should print out list of scheduled jobs
        assert out == "Scheduled jobs: 1, 2\n"
        # should exit 0
        assert not excinfo.value.code
        # shouldn't force
        assert fakejfu.call_args[1]['force'] is False

        if testargs[0] == 'update':
            # check critpath update restricts flavors
            modupd = copy.deepcopy(UPDATEJSON)
            modupd["update"]["critpath_groups"] = "critical-path-kde"
            fakejson.return_value = modupd
            with pytest.raises(SystemExit) as excinfo:
                cli.command_update_task(args)
            assert fakejfu.call_args[1]['flavors'] == {'kde', 'kde-live-iso'}
            # check critpath plus updatetl
            modupd["update"]["builds"][0]["nvr"] = "containernetworking-plugins-4.1.1-3.fc36"
            with pytest.raises(SystemExit) as excinfo:
                cli.command_update_task(args)
            assert fakejfu.call_args[1]['flavors'] == {'container', 'kde', 'kde-live-iso'}
            fakejson.return_value = UPDATEJSON

        # check 'flavor'
        args = cli.parse_args(
            testargs + ('--flavor', 'server')
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejfu.call_args[1]['flavors'] == ['server']

        # check 'force'
        args = cli.parse_args(
            testargs + ('--force',)
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejfu.call_args[1]['force'] is True

        # check 'openqa_hostname'
        args = cli.parse_args(
            testargs + ('--openqa-hostname', 'openqa.example')
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejfu.call_args[1]['openqa_hostname'] == 'openqa.example'

    @mock.patch('fedfind.helpers.download_json', return_value=UPDATEJSON, autospec=True)
    @mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1, 2], autospec=True)
    def test_command_update_norelease(self, fakejfu, fakejson, capsys):
        """Test update is OK with no release number."""
        args = cli.parse_args(('update', 'FEDORA-2017-b07d628952'))
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejfu.call_args[1]['version'] is None

    # this should not in fact get hit, but just in case we *do* break the code,
    # let's mock it to be safe...
    @mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1, 2], autospec=True)
    def test_command_update_nonint(self, fakejfu):
        """Test we exit 1 on a non-integer 'task' ID."""
        args = cli.parse_args(
            ['task', '123abc', '25']
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.command_update_task(args)
        # should exit 1
        assert excinfo.value.code == 1


class TestCommandFCOSBuild:
    """Tests for the command_fcosbuild function."""
    @mock.patch('fedora_openqa.schedule.jobs_from_fcosbuild', return_value=[1, 2], autospec=True)
    def test_fcosbuild(self, fakejff, capsys):
        """General tests for command_fcosbuild."""
        buildurl = "https://builds.coreos.fedoraproject.org/prod/streams/rawhide/builds/36.20211123.91.0/x86_64"
        args = cli.parse_args(["fcosbuild", buildurl])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_fcosbuild(args)
        (out, _) = capsys.readouterr()
        # first arg should be buildurl
        assert fakejff.call_args[0][0] == buildurl
        # flavors kwarg should be false-y (not, e.g., [None])
        assert not fakejff.call_args[1]["flavors"]
        # shouldn't force
        assert fakejff.call_args[1]["force"] is False
        # should print out list of scheduled jobs
        assert out == "Scheduled jobs: 1, 2\n"
        # should exit 0
        assert not excinfo.value.code

        # check 'flavors'
        args = cli.parse_args(["fcosbuild", buildurl, "--flavors", "foo,bar"])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_fcosbuild(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejff.call_args[1]["flavors"] == ["foo", "bar"]

        # check 'force'
        args = cli.parse_args(["fcosbuild", buildurl, "--force"])
        with pytest.raises(SystemExit) as excinfo:
            cli.command_fcosbuild(args)
        # should exit 0
        assert not excinfo.value.code
        assert fakejff.call_args[1]["force"] is True


class TestCommandReport:
    """Tests for the command_report function."""
    @pytest.mark.parametrize(
        "jobargs,argname,expecteds",
        # args, which kwarg we expect report function to get, list of
        # the expected values of specified kwarg for each expected
        # call to the report function
        [
            (["1", "2", "3"], "jobs", [[1, 2, 3]]),
            (
                ["Fedora-Rawhide-20170207.n.0", "Fedora-25-20170207.n.1"],
                "build",
                ["Fedora-Rawhide-20170207.n.0", "Fedora-25-20170207.n.1"]
            )
        ]
    )
    @pytest.mark.parametrize(
        "targargs,repwiki,reprdb",
        # args, should report_wiki be called, should report_resultsdb
        # be called
        [
            ([], False, False),
            (["--wiki"], True, False),
            (["--resultsdb"], False, True),
            (["--wiki", "--resultsdb"], True, True)
        ]
    )
    @pytest.mark.parametrize(
        "oqaargs,oqah,oqau",
        # args, expected openqa_hostname, expected openqa_baseurl
        [
            ([], None, None),
            (["--openqa-hostname", "test.ing"], "test.ing", None),
            (["--openqa-baseurl", "https://test.ing"], None, "https://test.ing"),
            (["--openqa-hostname", "test.ing", "--openqa-baseurl", "https://test.ing"],
             "test.ing", "https://test.ing")
        ]
    )
    @pytest.mark.parametrize(
        "wikiargs,wikih",
        # args, expected wiki_hostname
        [
            ([], None),
            (["--wiki-hostname", "test2.ing"], "test2.ing")
        ]
    )
    @pytest.mark.parametrize(
        "rdbargs,rdbu",
        # args, expected resultsdb_url
        [
            ([], None),
            (["--resultsdb-url", "test3.ing"], "test3.ing")
        ]
    )
    @mock.patch('fedora_openqa.report.wiki_report', autospec=True)
    @mock.patch('fedora_openqa.report.resultsdb_report', autospec=True)
    def test_variations(self, fakerdb, fakewiki, jobargs, argname, expecteds, targargs, repwiki, reprdb,
                        oqaargs, oqah, oqau, wikiargs, wikih, rdbargs, rdbu):
        """Okay, that was a lot of parametrization! But really we're
        just testing all possible arg combinations: both types of job
        arg (job IDs and build IDs), all four possible report targets
        (wiki, resultsdb, both, neither), all combinations of openqa
        hostname and baseurl, and both possibilities for wiki hostname
        and ResultsDB URL (specified or not). We test all possible
        combinations of these with each other by stacking decorators.
        """
        fakerdb.reset_mock()
        fakewiki.reset_mock()
        args = cli.parse_args(["report"] + targargs + oqaargs + wikiargs + rdbargs + jobargs)
        cli.command_report(args)

        # find the appropriate mock(s) and check they were called the
        # expected number of times
        fakes = []
        if repwiki:
            assert fakewiki.call_count == len(expecteds)
            fakes.append(fakewiki)
        if reprdb:
            assert fakerdb.call_count == len(expecteds)
            fakes.append(fakerdb)

        # check job arg parsed appropriately. for jobs, we expect one
        # call with a list of the job IDs as the jobs arg. For builds,
        # we expect as many calls as we included build IDs, with each
        # call specifying one build ID as the build arg.
        for fake in fakes:
            for (idx, expected) in enumerate(expecteds):
                assert fake.call_args_list[idx][1][argname] == expected

        # check the openQA, wiki and rdb args
        for fake in fakes:
            assert fake.call_args[1]['openqa_hostname'] == oqah
            assert fake.call_args[1]['openqa_baseurl'] == oqau
        if fakewiki in fakes:
            assert fakewiki.call_args[1]['wiki_hostname'] == wikih
        if fakerdb in fakes:
            assert fake.call_args[1]['resultsdb_url'] == rdbu


class TestCommandBlocked:
    """Tests for the command_blocked function."""

    @pytest.mark.parametrize("report", [True, False])
    @mock.patch("fedora_openqa.cli.OpenQA_Client", autospec=True)
    @mock.patch("requests.post", autospec=True)
    @mock.patch("fedfind.helpers.download_json", autospec=True)
    @mock.patch("fedora_openqa.report.resultsdb_report", autospec=True)
    def test_blocked(self, fakereport, fakedljson, fakepost, fakeclient, report):
        """
        Test the blocked subcommand works as expected, with a bunch of
        fake data that boils down to one 'missed' result we report as
        complete and one 'missed' result we report as not finished.
        Tests both with and without --report.
        """
        fakedljson.side_effect = [
            # fake getting two pages of data from bodhi, trimmed to
            # the fields we care about
            {
                "updates": [
                    {
                        "test_gating_status": "passed",
                        "critpath_groups": "core critical-path-build",
                        "release": {"version": "41"},
                        "alias": "FEDORA-2024-f39890a065",
                        "url": "https://bodhi.fedoraproject.org/updates/FEDORA-2024-f39890a065"
                    },
                    {
                        "test_gating_status": "failed",
                        "critpath_groups": "core critical-path-compose",
                        "release": {"version": "40"},
                        "alias": "FEDORA-2024-e1daa5bda2",
                        "url": "https://bodhi.fedoraproject.org/updates/FEDORA-2024-e1daa5bda2"
                    }
                ],
                "pages": 2
            },
            {
                "updates": [
                    {
                        "test_gating_status": "failed",
                        "critpath_groups": "",
                        "release": {"version": "39"},
                        "alias": "FEDORA-2024-6da0169ae7",
                        "url": "https://bodhi.fedoraproject.org/updates/FEDORA-2024-6da0169ae7"
                    },
                    {
                        "test_gating_status": "waiting",
                        "critpath_groups": "critical-path-gnome",
                        "release": {"version": "41"},
                        "alias": "FEDORA-2024-dd49d10899",
                        "url": "https://bodhi.fedoraproject.org/updates/FEDORA-2024-dd49d10899"
                    }
                ],
                "pages": 2
            }
        ]
        # fake getting appropriate greenwave responses for each of the
        # three updates we should get here for
        fakepost.return_value.json.side_effect = [
            {
                # trimmed, we only care if it's there or not
                "unsatisfied_requirements": [{"item": {"item": "FEDORA-2024-e1daa5bda2", "type": "bodhi_update"}}],
                "results": [
                    {
                        # should be ignored
                        "outcome": "INFO",
                        "ref_url": "https://openqa.fedoraproject.org/tests/2622431",
                        "submit_time": "2024-05-13T16:16:33.036460"
                    },
                    {
                        # should be considered
                        "outcome": "RUNNING",
                        "ref_url": "https://openqa.fedoraproject.org/tests/2622432",
                        # old enough to count
                        "submit_time": "2024-05-13T16:16:33.036460"
                    }
                ]
            },
            {
                "unsatisfied_requirements": [{"item": {"item": "FEDORA-2024-6da0169ae7", "type": "bodhi_update"}}],
                "results": [
                    {
                        # should be considered
                        "outcome": "QUEUED",
                        "ref_url": "https://openqa.fedoraproject.org/tests/2622433",
                        # too new
                        "submit_time": "2024-05-15T16:16:33.036460"
                    },
                    {
                        # should be considered
                        "outcome": "QUEUED",
                        "ref_url": "https://openqa.fedoraproject.org/tests/2622434",
                        # old enough
                        "submit_time": "2024-05-13T16:16:33.036460"
                    }
                ]
            },
            {
                # should be ignored
                "unsatisfied_requirements": [],
                "results": [
                    {
                        # would be considered if there were unsatisfied reqs
                        "outcome": "RUNNING",
                        "ref_url": "https://openqa.fedoraproject.org/tests/2622433",
                        # old enough
                        "submit_time":"2024-05-13T16:16:33.036460"
                    }
                ]
            }
        ]
        # fake appropriate openQA client responses for the two jobs we
        # should get here for
        fakeclient().get_jobs.side_effect = [
            [{"id": 2622432, "result": "passed"}],
            [{"id": 2622434, "result": "none"}]
        ]
        command = ["blocked"]
        if report:
            command.append("--report")
        args = cli.parse_args(command)
        with freeze_time("2024-05-15 00:00:00", tz_offset=0):
            cli.command_blocked(args)
        assert fakedljson.call_count == 2
        url = "https://bodhi.fedoraproject.org/updates/?status=testing&critpath=True"
        # ew, tuple syntax
        assert fakedljson.call_args_list == [((url,),), ((f"{url}&page=2",),)]
        assert fakepost.call_count == 3
        assert fakeclient().get_jobs.call_count == 2
        assert fakeclient().get_jobs.call_args_list == [
            ({"jobs": ["2622432"], "filter_dupes": False},),
            ({"jobs": ["2622434"], "filter_dupes": False},)
        ]
        if report:
            assert fakereport.call_count == 1
            # check we actually try to report the right job
            assert fakereport.call_args == (
                {
                    "resultsdb_url": None,
                    "openqa_hostname": None,
                    "openqa_baseurl": None,
                    "jobs": [2622432],
                    "do_report": True
                },
            )
        else:
            assert fakereport.call_count == 0
# vim: set textwidth=120 ts=8 et sw=4:
