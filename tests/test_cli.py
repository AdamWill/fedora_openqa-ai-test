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

"""Tests for the CLI code."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports

# external imports
import mock
import pytest

# 'internal' imports
import fedora_openqa.cli as cli


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

@mock.patch('fedora_openqa.schedule.jobs_from_update', return_value=[1, 2], autospec=True)
def test_command_update(fakejfu, capsys):
    """Test the command_update function."""
    args = cli.parse_args(
        ['update', 'FEDORA-2017-b07d628952', '25']
    )
    with pytest.raises(SystemExit) as excinfo:
        cli.command_update(args)
    (out, _) = capsys.readouterr()
    # should print out list of scheduled jobs
    assert out == "Scheduled jobs: 1, 2\n"
    # should exit 0
    assert not excinfo.value.code
    # shouldn't force
    assert fakejfu.call_args[1]['force'] is False

    # check 'flavor'
    args = cli.parse_args(
        ['update', 'FEDORA-2017-b07d628952', '25', '--flavor', 'server']
    )
    with pytest.raises(SystemExit) as excinfo:
        cli.command_update(args)
    # should exit 0
    assert not excinfo.value.code
    assert fakejfu.call_args[1]['flavors'] == ['server']

    # check 'force'
    args = cli.parse_args(
        ['update', 'FEDORA-2017-b07d628952', '25', '--force']
    )
    with pytest.raises(SystemExit) as excinfo:
        cli.command_update(args)
    # should exit 0
    assert not excinfo.value.code
    assert fakejfu.call_args[1]['force'] is True

    # check 'openqa_hostname'
    args = cli.parse_args(
        ['update', 'FEDORA-2017-b07d628952', '25', '--openqa-hostname', 'openqa.example']
    )
    with pytest.raises(SystemExit) as excinfo:
        cli.command_update(args)
    # should exit 0
    assert not excinfo.value.code
    assert fakejfu.call_args[1]['openqa_hostname'] == 'openqa.example'

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
        (["--openqa-hostname", "test.ing", "--openqa-baseurl", "https://test.ing"], "test.ing", "https://test.ing")
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
def test_variations(fakerdb, fakewiki, jobargs, argname, expecteds, targargs, repwiki, reprdb,
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

# vim: set textwidth=120 ts=8 et sw=4:
