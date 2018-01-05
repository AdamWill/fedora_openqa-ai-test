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

"""Tests for the scheduling code."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports

# external imports
import fedfind.release
import openqa_client
import mock
import pytest

# 'internal' imports
import fedora_openqa.schedule as schedule

COMPURL = 'https://kojipkgs.fedoraproject.org/compose/branched/Fedora-25-20161115.n.0/compose/'

@pytest.mark.usefixtures("ffmock02")
class TestGetImages:
    """Tests for _get_images."""

    def test_basic(self):
        """Test the basic case, with the ffmock02 data mock (real data
        from a circa F25 Branched nightly with lots of images) and
        default WANTED.
        """
        rel = fedfind.release.get_release(cid='Fedora-25-20161115.n.0')
        ret = schedule._get_images(rel)
        assert ret == [
            (
                "Server-boot-iso",
                "x86_64",
                6,
                {
                    "ISO_URL": COMPURL + "Server/x86_64/iso/Fedora-Server-netinst-x86_64-25-20161115.n.0.iso"
                },
                "Server",
                "boot"
            ),
            (
                "Server-dvd-iso",
                "x86_64",
                10,
                {
                    "ISO_URL": COMPURL + "Server/x86_64/iso/Fedora-Server-dvd-x86_64-25-20161115.n.0.iso"
                },
                "Server",
                "dvd"
            ),
            (
                "Server-boot-iso",
                "i386",
                6,
                {
                    "ISO_URL": COMPURL + "Server/i386/iso/Fedora-Server-netinst-i386-25-20161115.n.0.iso"
                },
                "Server",
                "boot"
            ),
            (
                "Server-dvd-iso",
                "i386",
                10,
                {
                    "ISO_URL": COMPURL + "Server/i386/iso/Fedora-Server-dvd-i386-25-20161115.n.0.iso"
                },
                "Server",
                "dvd"
            ),
            (
                "Everything-boot-iso",
                "x86_64",
                8,
                {
                    "ISO_URL": COMPURL + "Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-25-20161115.n.0.iso"
                },
                "Everything",
                "boot"
            ),
            (
                "Everything-boot-iso",
                "i386",
                8,
                {
                    "ISO_URL": COMPURL + "Everything/i386/iso/Fedora-Everything-netinst-i386-25-20161115.n.0.iso"
                },
                "Everything",
                "boot"
            ),
            (
                "Workstation-live-iso",
                "x86_64",
                0,
                {
                    "ISO_URL": COMPURL + "Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-25-20161115.n.0.iso"
                },
                "Workstation",
                "live"
            ),
            (
                "Workstation-boot-iso",
                "x86_64",
                0,
                {
                    "ISO_URL": COMPURL + "Workstation/x86_64/iso/Fedora-Workstation-netinst-x86_64-25-20161115.n.0.iso"
                },
                "Workstation",
                "boot"
            ),
            (
                "Workstation-live-iso",
                "i386",
                0,
                {
                    "ISO_URL": COMPURL + "Workstation/i386/iso/Fedora-Workstation-Live-i386-25-20161115.n.0.iso"
                },
                "Workstation",
                "live"
            ),
            (
                "Workstation-boot-iso",
                "i386",
                0,
                {
                    "ISO_URL": COMPURL + "Workstation/i386/iso/Fedora-Workstation-netinst-i386-25-20161115.n.0.iso"
                },
                "Workstation",
                "boot"
            ),
            (
                "KDE-live-iso",
                "x86_64",
                0,
                {
                    "ISO_URL": COMPURL + "Spins/x86_64/iso/Fedora-KDE-Live-x86_64-25-20161115.n.0.iso"
                },
                "KDE",
                "live"
            ),
            (
                "KDE-live-iso",
                "i386",
                0,
                {
                    "ISO_URL": COMPURL + "Spins/i386/iso/Fedora-KDE-Live-i386-25-20161115.n.0.iso"
                },
                "KDE",
                "live"
            ),
            (
                "Minimal-raw_xz-raw.xz",
                "armhfp",
                0,
                {
                    "KERNEL": "Fedora-25-20161115.n.0.armhfp.vmlinuz",
                    "INITRD": "Fedora-25-20161115.n.0.armhfp.initrd.img",
                    "INITRD_URL": COMPURL + "Everything/armhfp/os/images/pxeboot/initrd.img",
                    # pylint: disable=line-too-long
                    "HDD_2_DECOMPRESS_URL": COMPURL + "Spins/armhfp/images/Fedora-Minimal-armhfp-25-20161115.n.0-sda.raw.xz",
                    "KERNEL_URL": COMPURL + "Everything/armhfp/os/images/pxeboot/vmlinuz"
                },
                "Minimal",
                "raw-xz"
            )
        ]

    def test_wanted_arg(self):
        """Test custom WANTED passed by arg is respected."""
        wanted = [
            {
                "match": {
                    "subvariant": "Server",
                    "type": "boot",
                    "format": "iso",
                    "arch": "x86_64",
                },
                "score": 7,
            },
        ]
        rel = fedfind.release.get_release(cid='Fedora-25-20161115.n.0')
        ret = schedule._get_images(rel, wanted)
        assert ret == [
            (
                "Server-boot-iso",
                "x86_64",
                7,
                {
                    "ISO_URL": COMPURL + "Server/x86_64/iso/Fedora-Server-netinst-x86_64-25-20161115.n.0.iso"
                },
                "Server",
                "boot"
            ),
        ]


def test_find_duplicate_jobs():
    """Tests for _find_duplicate_jobs."""
    # autospecced OpenQA_Client mock, see:
    # https://docs.python.org/3/library/unittest.mock.html#autospeccing
    client = mock.create_autospec(openqa_client.client.OpenQA_Client)

    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'state': 'done'}]}
    # check ISO case
    ret = schedule._find_duplicate_jobs(client, {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 1
    assert client.openqa_request.call_args[1]['params'] == {'iso': 'some.iso'}
    # HDD_1 case
    ret = schedule._find_duplicate_jobs(client, {'HDD_1': 'somefile.img'}, 'someflavor')
    assert len(ret) == 1
    assert client.openqa_request.call_args[1]['params'] == {'hdd_1': 'somefile.img'}
    client.openqa_request.reset_mock()
    # HDD_1_DECOMPRESS_URL case
    ret = schedule._find_duplicate_jobs(
        client, {'HDD_1_DECOMPRESS_URL': 'https://some.url/somefile.img.gz'}, 'someflavor')
    assert len(ret) == 1

    # shouldn't find any dupes if flavor differs
    ret = schedule._find_duplicate_jobs(client, {'ISO_URL': 'https://some.url/some.iso'}, 'otherflavor')
    assert len(ret) == 0

    # job in 'cancelled' state isn't a dupe
    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'state': 'cancelled'}]}
    ret = schedule._find_duplicate_jobs(client, {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 0

    # user-cancelled job (which is a result not a state?) isn't either
    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'result': 'user_cancelled'}]}
    ret = schedule._find_duplicate_jobs(client, {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 0


@mock.patch('fedfind.helpers.get_current_release', return_value=25, autospec=True)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
@mock.patch('fedora_openqa.schedule._find_duplicate_jobs', return_value=[], autospec=True)
def test_run_openqa_jobs(fakedupes, fakeclient, fakecurr, ffmock02):
    """Tests for run_openqa_jobs."""
    # get our expected images from the ffmock02 image list.
    rel = fedfind.release.get_release(cid='Fedora-25-20161115.n.0')
    images = schedule._get_images(rel)

    # OpenQA_Client mock 'instance' is the class mock return value
    instance = fakeclient.return_value

    for (flavor, arch, _, param_urls, subvariant, imagetype) in images:
        instance.reset_mock()
        schedule.run_openqa_jobs(
            param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location)
        assert instance.openqa_request.call_count == 1
        expdict = {
            'DISTRI': 'fedora',
            'VERSION': '25',
            'FLAVOR': flavor,
            'ARCH': arch if arch != 'armhfp' else 'arm',
            'BUILD': 'Fedora-25-20161115.n.0',
            'LOCATION': rel.location,
            'CURRREL': '25',
            'PREVREL': '24',
            'RAWREL': '26',
            'SUBVARIANT': subvariant,
            'IMAGETYPE': imagetype,
            '_ONLY_OBSOLETE_SAME_BUILD': '1',
        }
        expdict.update(param_urls)
        assert instance.openqa_request.call_args[0] == ('POST', 'isos', expdict)

    # check no jobs scheduled when dupes are found
    instance.reset_mock()
    fakedupes.return_value = [{'id': 1}]
    (flavor, arch, _, param_urls, subvariant, imagetype) = images[0]
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location)
    assert instance.openqa_request.call_count == 0

    # check force overrides dupe detection
    instance.reset_mock()
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location,
        force=True)
    assert instance.openqa_request.call_count == 1

    # check extraparams handling
    instance.reset_mock()
    fakedupes.return_value = []
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location,
        extraparams={'EXTRA': 'here'})
    assert instance.openqa_request.call_args[0][2]['EXTRA'] == 'here'
    assert instance.openqa_request.call_args[0][2]['BUILD'] == 'Fedora-25-20161115.n.0-EXTRA'

    # check openqa_hostname is passed through
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location,
        openqa_hostname='somehost')
    assert fakeclient.call_args[0][0] == 'somehost'

    # check we set MODULAR param for modular composes
    instance.reset_mock()
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Modular-25-20161115.n.0', '25', rel.location)
    assert instance.openqa_request.call_args[0][2]['MODULAR'] == '1'

    # check we don't crash or fail to schedule if get_current_release
    # fails
    instance.reset_mock()
    fakecurr.side_effect = ValueError("Well, that was unfortunate")
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-25-20161115.n.0', '25', rel.location)
    assert instance.openqa_request.call_count == 1
    assert instance.openqa_request.call_args[0][2]['CURRREL'] == 'FEDFINDERROR'

@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
def test_jobs_from_compose(fakerun, ffmock02):
    """Tests for jobs_from_compose."""
    # simple case
    ret = schedule.jobs_from_compose(COMPURL)

    # 13 images, 2 universal arches
    assert fakerun.call_count == 15

    # the list of job ids should be 15 1s, as each fakerun call
    # returns [1]
    assert ret == ('Fedora-25-20161115.n.0', [1 for _ in range(15)])

    for argtup in fakerun.call_args_list:
        # check rel identification bits got passed properly
        assert argtup[0][-3:] == ('Fedora-25-20161115.n.0', '25', COMPURL)

    univs = [argtup[0][0]['ISO_URL'] for argtup in fakerun.call_args_list if argtup[0][1] == 'universal']
    assert univs == [
        COMPURL + 'Server/x86_64/iso/Fedora-Server-dvd-x86_64-25-20161115.n.0.iso',
        COMPURL + 'Server/i386/iso/Fedora-Server-dvd-i386-25-20161115.n.0.iso'
    ]

    # check force, extraparams and openqa_hostname are passed through
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(
        COMPURL, force=True, extraparams={'EXTRA': 'here'}, openqa_hostname='somehost')
    for argtup in fakerun.call_args_list:
        assert argtup[1]['force'] is True
        assert argtup[1]['extraparams'] == {'EXTRA': 'here'}
        assert argtup[1]['openqa_hostname'] == 'somehost'

    # check triggerexception is raised when appropriate
    with mock.patch('fedfind.release.get_release', side_effect=ValueError("Oops!")):
        with pytest.raises(schedule.TriggerException):
            ret = schedule.jobs_from_compose(COMPURL)

    with mock.patch('fedora_openqa.schedule._get_images', return_value=[]):
        with pytest.raises(schedule.TriggerException):
            ret = schedule.jobs_from_compose(COMPURL)

@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
@mock.patch.object(fedfind.release.BranchedNightly, 'type', 'production')
def test_jobs_from_compose_tag(fakeclient, fakerun, ffmock02):
    """Check that we tag candidate composes as 'important'."""
    ret = schedule.jobs_from_compose(COMPURL)
    assert ret == ('Fedora-25-20161115.n.0', [1 for _ in range(15)])
    # find the args that openqa_request was last called with
    reqargs = fakeclient.return_value.openqa_request.call_args
    assert reqargs[0] == ('POST', 'groups/1/comments')
    assert reqargs[1]['params'] == {'text': 'tag:Fedora-25-20161115.n.0:important:candidate'}

@mock.patch('fedfind.helpers.get_current_release', return_value=25)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
def test_jobs_from_update(fakeclient, fakecurr):
    """Tests for jobs_from_update."""
    # the OpenQA_Client instance mock
    fakeinst = fakeclient.return_value
    # for now, return no 'jobs' (for the dupe query), one 'id' (for
    # the post request)
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    # simple case
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25')
    # should get two jobs (as we schedule for two flavors by default)
    assert ret == [1, 1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # two flavors by default, two calls
    assert len(posts) == 2
    parmdicts = [call[0][2] for call in posts]
    parmdicts.sort()
    assert parmdicts == [
        {
            'DISTRI': 'fedora',
            'VERSION': '25',
            'ARCH': 'x86_64',
            'BUILD': 'Update-FEDORA-2017-b07d628952',
            'ADVISORY': 'FEDORA-2017-b07d628952',
            '_ONLY_OBSOLETE_SAME_BUILD': '1',
            'START_AFTER_TEST': '',
            'HDD_1': 'disk_f25_server_3_x86_64.img',
            'FLAVOR': 'updates-server',
        },
        {
            'DISTRI': 'fedora',
            'VERSION': '25',
            'ARCH': 'x86_64',
            'BUILD': 'Update-FEDORA-2017-b07d628952',
            'ADVISORY': 'FEDORA-2017-b07d628952',
            '_ONLY_OBSOLETE_SAME_BUILD': '1',
            'START_AFTER_TEST': '',
            'HDD_1': 'disk_f25_desktop_4_x86_64.img',
            'FLAVOR': 'updates-workstation',
            'DESKTOP': 'gnome',
        }
    ]

    # test DEVELOPMENT var set when release is higher than current
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '26')
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    parmdicts = [call[0][2] for call in posts]
    assert all(parmdict.get('DEVELOPMENT') == 1 for parmdict in parmdicts)

    # check we don't crash or fail to schedule if get_current_release
    # fails
    fakeinst.openqa_request.reset_mock()
    fakecurr.side_effect = ValueError("Well, that was unfortunate")
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '26')
    assert ret == [1, 1]
    fakecurr.side_effect = None

    # test 'flavors'
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', flavors=['server'])
    # should get one job
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    # check parm dict FLAVOR value
    assert posts[0][0][2]['FLAVOR'] == 'updates-server'

    # test dupe detection and 'force'
    fakeinst.openqa_request.reset_mock()
    # this looks like a 'dupe' for the server flavor
    fakeinst.openqa_request.return_value = {
        'jobs': [
            {
                'settings': {
                    'FLAVOR': 'updates-server',
                },
            },
        ],
        'ids': [1],
    }
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25')
    # should get one job, as we shouldn't POST for server
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    # check parm dict FLAVOR value
    assert posts[0][0][2]['FLAVOR'] == 'updates-workstation'
    # now try with force=True
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', force=True)
    # should get two jobs this time
    assert ret == [1, 1]

    # test extraparams
    fakeinst.openqa_request.reset_mock()
    # set the openqa_request return value back to the no-dupes version
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', flavors=['server'], extraparams={'FOO': 'bar'})
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # check parm dict values
    assert posts[0][0][2]['BUILD'] == 'Update-FEDORA-2017-b07d628952-EXTRA'
    assert posts[0][0][2]['FOO'] == 'bar'

    # test openqa_hostname
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', openqa_hostname='openqa.example')
    assert fakeclient.call_args[0][0] == 'openqa.example'

    # test arch
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', arch='ppc64le')
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # check parm dict values
    assert posts[0][0][2]['ARCH'] == 'ppc64le'
    assert posts[0][0][2]['HDD_1'] in ['disk_f25_server_3_ppc64le.img', 'disk_f25_desktop_4_ppc64le.img']

# vim: set textwidth=120 ts=8 et sw=4:
