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
# pylint: disable=protected-access, unused-argument, too-many-lines, too-many-locals, too-many-statements

"""Tests for the scheduling code."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
from unittest import mock

# external imports
import fedfind.release
import openqa_client
import pytest

# 'internal' imports
import fedora_openqa.schedule as schedule
from fedora_openqa.schedule import UPDATE_FLAVORS

# these are just used to keep some line lengths short...
COMPURL = 'https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20230502.n.0/compose/'
COMPVR = 'Rawhide-20230502.n.0'
# trimmed Bodhi response for FEDORA-2017-b07d628952, jobs_from_update
# uses this to determine the release and the NVRs in the update. This
# is tweaked from the real output to include 21 builds (one more than
# the chunk size for splitting ADVISORY_NVRS).
UPDATENVRS_1 = (
    'cockpit-129-1.fc25',
    'systemd-231-7.fc25',
    'chirp-20171204-1.fc25',
    'whois-5.2.19-1.fc25',
    'lcgdm-1.9.1-1.fc25',
    'redis-4.0.6-1.fc25',
    'newsbeuter-2.9-6.fc25',
    'bandit-1.4.0-5.fc25',
    'pdc-client-1.8.0-4.fc25',
    'cinnamon-3.6.6-12.fc25',
    'modulemd-1.3.3-1.fc25',
    'libextractor-1.6-2.fc25',
    'python-rmtest-0.6.6-1.fc25',
    'dnssec-trigger-0.15-1.fc25',
    'lynx-2.8.9-0.20.dev16.fc25',
    'perl-Digest-SHA-6.00-1.fc25',
    'torrent-file-editor-0.3.9-1.fc25',
    'libverto-jsonrpc-0.1.0-16.fc25',
    'geany-1.32-1.fc25',
    'geany-plugins-1.32-1.fc25',
)
UPDATENVRS_2 = ('python-yattag-1.9.2-1.fc25',)
UPDATEJSON = {
    'builds': [
        {
            'nvr': nvr,
            'release_id': 15,
            'signed': True,
            'type': 'rpm',
            'epoch': 0
        } for nvr in UPDATENVRS_1 + UPDATENVRS_2
    ],
    'release': {
        'version': '25'
    }
}
# trimmed CoreOS build metadata JSON, used for scheduling CoreOS jobs
COREOSJSON = {
    "buildid": "36.20211123.91.0",
    "images": {
        "live-iso": {
            "path": "fedora-coreos-36.20211123.91.0-live.x86_64.iso",
            "sha256": "ad0d16c772c1ba6c3f1189d6de37e25e251b3d11ce96b9fe2c44fb4178a320b9"
        }
    },
    "coreos-assembler.basearch": "x86_64"
}

@pytest.mark.usefixtures("ffmock02")
class TestGetImages:
    """Tests for _get_images."""

    def test_basic(self):
        """Test the basic case, with the ffmock02 data mock (real data
        from a circa F39 Rawhide nightly with lots of images) and
        default WANTED.
        """
        rel = fedfind.release.get_release(cid='Fedora-Rawhide-20230502.n.0')
        ret = schedule._get_images(rel)
        assert ret == [
            (
                "Server-boot-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Server/x86_64/iso/Fedora-Server-netinst-x86_64-{COMPVR}.iso"
                },
                "Server",
                "boot"
            ),
            (
                "Server-dvd-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Server/x86_64/iso/Fedora-Server-dvd-x86_64-{COMPVR}.iso"
                },
                "Server",
                "dvd"
            ),
            (
                "Everything-boot-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-{COMPVR}.iso"
                },
                "Everything",
                "boot"
            ),
            (
                "Workstation-live-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-{COMPVR}.iso"
                },
                "Workstation",
                "live"
            ),
            (
                "KDE-live-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Spins/x86_64/iso/Fedora-KDE-Live-x86_64-{COMPVR}.iso"
                },
                "KDE",
                "live"
            ),
            (
                "Silverblue-dvd_ostree-iso",
                "x86_64",
                {
                    "ISO_URL": f"{COMPURL}Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-{COMPVR}.iso"
                },
                "Silverblue",
                "dvd-ostree"
            ),
            (
                "Cloud_Base-qcow2-qcow2",
                "x86_64",
                {
                    "HDD_2_URL": f"{COMPURL}Cloud/x86_64/images/Fedora-Cloud-Base-{COMPVR}.x86_64.qcow2"
                },
                "Cloud_Base",
                "qcow2"
            ),
            (
                "Everything-boot-iso",
                "ppc64le",
                {
                    "ISO_URL": f"{COMPURL}Everything/ppc64le/iso/Fedora-Everything-netinst-ppc64le-{COMPVR}.iso"
                },
                "Everything",
                "boot"
            ),
            (
                "Workstation-live-iso",
                "ppc64le",
                {
                    "ISO_URL": f"{COMPURL}Workstation/ppc64le/iso/Fedora-Workstation-Live-ppc64le-{COMPVR}.iso"
                },
                "Workstation",
                "live"
            ),
            (
                "Server-boot-iso",
                "ppc64le",
                {
                    "ISO_URL": f"{COMPURL}Server/ppc64le/iso/Fedora-Server-netinst-ppc64le-{COMPVR}.iso"
                },
                "Server",
                "boot"
            ),
            (
                "Server-dvd-iso",
                "ppc64le",
                {
                    "ISO_URL": f"{COMPURL}Server/ppc64le/iso/Fedora-Server-dvd-ppc64le-{COMPVR}.iso"
                },
                "Server",
                "dvd"
            ),
            (
                "Cloud_Base-qcow2-qcow2",
                "ppc64le",
                {
                    "HDD_2_URL": f"{COMPURL}Cloud/ppc64le/images/Fedora-Cloud-Base-{COMPVR}.ppc64le.qcow2"
                },
                "Cloud_Base",
                "qcow2"
            ),
            (
                "Silverblue-dvd_ostree-iso",
                "ppc64le",
                {
                    "ISO_URL": f"{COMPURL}Silverblue/ppc64le/iso/Fedora-Silverblue-ostree-ppc64le-{COMPVR}.iso"
                },
                "Silverblue",
                "dvd-ostree"
            ),
            (
                "Minimal-raw_xz-raw.xz",
                "aarch64",
                {
                    "HDD_2_DECOMPRESS_URL": f"{COMPURL}Spins/aarch64/images/Fedora-Minimal-{COMPVR}.aarch64.raw.xz"
                },
                "Minimal",
                "raw-xz"
            ),
            (
                "Server-boot-iso",
                "aarch64",
                {
                    "ISO_URL": f"{COMPURL}Server/aarch64/iso/Fedora-Server-netinst-aarch64-{COMPVR}.iso"
                },
                "Server",
                "boot"
            ),
            (
                "Server-dvd-iso",
                "aarch64",
                {
                    "ISO_URL": f"{COMPURL}Server/aarch64/iso/Fedora-Server-dvd-aarch64-{COMPVR}.iso"
                },
                "Server",
                "dvd"
            ),
            (
                "Server-raw_xz-raw.xz",
                "aarch64",
                {
                    "HDD_2_DECOMPRESS_URL": f"{COMPURL}Server/aarch64/images/Fedora-Server-{COMPVR}.aarch64.raw.xz"
                },
                "Server",
                "raw-xz"
            ),
            (
                "Workstation-raw_xz-raw.xz",
                "aarch64",
                {
                    # pylint: disable=line-too-long
                    "HDD_2_DECOMPRESS_URL": f"{COMPURL}Workstation/aarch64/images/Fedora-Workstation-{COMPVR}.aarch64.raw.xz"
                },
                "Workstation",
                "raw-xz"
            ),
            (
                "Cloud_Base-qcow2-qcow2",
                "aarch64",
                {
                    "HDD_2_URL": f"{COMPURL}Cloud/aarch64/images/Fedora-Cloud-Base-{COMPVR}.aarch64.qcow2"
                },
                "Cloud_Base",
                "qcow2"
            )
        ]

    def test_wanted_arg(self):
        """Test custom WANTED passed by arg is respected."""
        wanted = [
            {
                "match": {
                    "subvariant": "Minimal",
                    "type": "raw-xz",
                    "format": "raw.xz",
                    "arch": "aarch64",
                },
            },
        ]
        rel = fedfind.release.get_release(cid='Fedora-Rawhide-20230502.n.0')
        ret = schedule._get_images(rel, wanted)
        assert ret == [
            (
                "Minimal-raw_xz-raw.xz",
                "aarch64",
                {"HDD_2_DECOMPRESS_URL": f"{COMPURL}Spins/aarch64/images/Fedora-Minimal-{COMPVR}.aarch64.raw.xz"},
                "Minimal",
                "raw-xz"
            ),
        ]


def test_find_duplicate_jobs():
    """Tests for _find_duplicate_jobs."""
    # autospecced OpenQA_Client mock, see:
    # https://docs.python.org/3/library/unittest.mock.html#autospeccing
    client = mock.create_autospec(openqa_client.client.OpenQA_Client)

    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'state': 'done'}]}
    # check ISO case
    ret = schedule._find_duplicate_jobs(client, 'build', {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 1
    assert client.openqa_request.call_args[1]['params'] == {'iso': 'some.iso', 'build': 'build'}
    # HDD_1 case
    ret = schedule._find_duplicate_jobs(client, 'build', {'HDD_1': 'somefile.img'}, 'someflavor')
    assert len(ret) == 1
    assert client.openqa_request.call_args[1]['params'] == {'hdd_1': 'somefile.img', 'build': 'build'}
    # HDD_2 case
    ret = schedule._find_duplicate_jobs(client, 'build', {'HDD_2': 'somefile.img'}, 'someflavor')
    assert len(ret) == 1
    assert client.openqa_request.call_args[1]['params'] == {'hdd_2': 'somefile.img', 'build': 'build'}
    client.openqa_request.reset_mock()
    # HDD_1_DECOMPRESS_URL case
    ret = schedule._find_duplicate_jobs(
        client, 'build', {'HDD_1_DECOMPRESS_URL': 'https://some.url/somefile.img.gz'}, 'someflavor')
    assert len(ret) == 1
    # HDD_2_DECOMPRESS_URL case
    ret = schedule._find_duplicate_jobs(
        client, 'build', {'HDD_2_DECOMPRESS_URL': 'https://some.url/somefile.img.gz'}, 'someflavor')
    assert len(ret) == 1

    # shouldn't find any dupes if flavor differs
    ret = schedule._find_duplicate_jobs(client, 'build', {'ISO_URL': 'https://some.url/some.iso'}, 'otherflavor')
    assert len(ret) == 0

    # job in 'cancelled' state isn't a dupe
    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'state': 'cancelled'}]}
    ret = schedule._find_duplicate_jobs(client, 'build', {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 0

    # user-cancelled job (which is a result not a state?) isn't either
    client.openqa_request.return_value = {'jobs': [{'settings': {'FLAVOR': 'someflavor'}, 'result': 'user_cancelled'}]}
    ret = schedule._find_duplicate_jobs(client, 'build', {'ISO_URL': 'https://some.url/some.iso'}, 'someflavor')
    assert len(ret) == 0


@mock.patch('fedfind.helpers.get_current_release', return_value=38, autospec=True)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
@mock.patch('fedora_openqa.schedule._find_duplicate_jobs', return_value=[], autospec=True)
def test_run_openqa_jobs(fakedupes, fakeclient, fakecurr, ffmock02):
    """Tests for run_openqa_jobs."""
    # get our expected images from the ffmock02 image list.
    rel = fedfind.release.get_release(cid='Fedora-Rawhide-20230502.n.0')
    images = schedule._get_images(rel)

    # OpenQA_Client mock 'instance' is the class mock return value
    instance = fakeclient.return_value

    for (flavor, arch, param_urls, subvariant, imagetype) in images:
        instance.reset_mock()
        schedule.run_openqa_jobs(
            param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location)
        assert instance.openqa_request.call_count == 1
        expdict = {
            'DISTRI': 'fedora',
            'VERSION': 'Rawhide',
            'FLAVOR': flavor,
            'ARCH': arch,
            'BUILD': 'Fedora-Rawhide-20230502.n.0',
            'LOCATION': rel.location,
            'CURRREL': '38',
            'RAWREL': '39',
            'UP1REL': '38',
            'UP2REL': '37',
            'SUBVARIANT': subvariant,
            'IMAGETYPE': imagetype,
            'QEMU_HOST_IP': '172.16.2.2',
            'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24',
            '_OBSOLETE': '1',
            '_ONLY_OBSOLETE_SAME_BUILD': '1',
        }
        expdict.update(param_urls)
        assert instance.openqa_request.call_args[0] == ('POST', 'isos', expdict)

    # check we include LABEL when appropriate
    instance.reset_mock()
    (flavor, arch, param_urls, subvariant, imagetype) = images[0]
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location,
        label="RC-1.5")
    assert instance.openqa_request.call_count == 1
    assert instance.openqa_request.call_args[0][2]['LABEL'] == 'RC-1.5'

    # check no jobs scheduled when dupes are found
    instance.reset_mock()
    fakedupes.return_value = [{'id': 1}]
    (flavor, arch, param_urls, subvariant, imagetype) = images[0]
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location)
    assert instance.openqa_request.call_count == 0

    # check force overrides dupe detection
    instance.reset_mock()
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location,
        force=True)
    assert instance.openqa_request.call_count == 1

    # check extraparams handling
    instance.reset_mock()
    fakedupes.return_value = []
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location,
        extraparams={'EXTRA': 'here'})
    assert instance.openqa_request.call_args[0][2]['EXTRA'] == 'here'
    assert instance.openqa_request.call_args[0][2]['BUILD'] == 'Fedora-Rawhide-20230502.n.0-EXTRA'

    # check openqa_hostname is passed through
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location,
        openqa_hostname='somehost')
    assert fakeclient.call_args[0][0] == 'somehost'

    # check we don't crash or fail to schedule if get_current_release
    # fails
    instance.reset_mock()
    fakecurr.side_effect = ValueError("Well, that was unfortunate")
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, 'Fedora-Rawhide-20230502.n.0', 'Rawhide', rel.location)
    assert instance.openqa_request.call_count == 1
    assert instance.openqa_request.call_args[0][2]['CURRREL'] == 'FEDFINDERROR'


@mock.patch('fedfind.helpers.get_current_release', return_value=25)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
@mock.patch('fedora_openqa.schedule._find_duplicate_jobs', return_value=[], autospec=True)
def test_run_openqa_jobs_rawhide_vers(fakedupes, fakeclient, fakecurr, ffmock):
    """Test the _get_releases stuff with a Rawhide compose."""
    rel = fedfind.release.get_release(cid="Fedora-Rawhide-20170207.n.0")
    images = schedule._get_images(rel)
    # OpenQA_Client mock 'instance' is the class mock return value
    instance = fakeclient.return_value
    (flavor, arch, param_urls, subvariant, imagetype) = images[0]
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, "Fedora-Rawhide-20170207.n.0", "Rawhide", rel.location)
    assert instance.openqa_request.call_args[0][2]["CURRREL"] == "25"
    assert instance.openqa_request.call_args[0][2]["RAWREL"] == "26"
    assert instance.openqa_request.call_args[0][2]["UP1REL"] == "25"
    assert instance.openqa_request.call_args[0][2]["UP2REL"] == "24"
    # now test outcome if fedfind is busted
    instance.reset_mock()
    fakecurr.side_effect = ValueError("Well, that was unfortunate")
    schedule.run_openqa_jobs(
        param_urls, flavor, arch, subvariant, imagetype, "Fedora-Rawhide-20170207.n.0", "Rawhide", rel.location)
    assert instance.openqa_request.call_args[0][2]["CURRREL"] == "FEDFINDERROR"
    assert instance.openqa_request.call_args[0][2]["RAWREL"] == "rawhide"
    assert instance.openqa_request.call_args[0][2]["UP1REL"] == "FEDFINDERROR"
    assert instance.openqa_request.call_args[0][2]["UP2REL"] == "FEDFINDERROR"


@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
def test_jobs_from_compose(fakerun, ffmock02):
    """Tests for jobs_from_compose."""
    # simple case
    ret = schedule.jobs_from_compose(COMPURL)

    # 7 images, 1 x86_64 upgrade flavor, 1 universal arch
    assert fakerun.call_count == 9

    # the list of job ids should be 9 1s, as each fakerun call
    # returns [1]
    assert ret == ('Fedora-Rawhide-20230502.n.0', [1 for _ in range(9)])

    for argtup in fakerun.call_args_list:
        # check rel identification bits got passed properly
        assert argtup[0][-3:] == ('Fedora-Rawhide-20230502.n.0', 'Rawhide', COMPURL)

    univ = [argtup[0][0] for argtup in fakerun.call_args_list if argtup[0][1] == 'universal'][0]
    # we should not schedule any image for 'universal' these days
    assert "ISO_URL" not in univ

    # check force, extraparams and openqa_hostname are passed through
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(
        COMPURL, force=True, extraparams={'EXTRA': 'here'}, openqa_hostname='somehost')
    for argtup in fakerun.call_args_list:
        assert argtup[1]['force'] is True
        assert argtup[1]['extraparams'] == {'EXTRA': 'here'}
        assert argtup[1]['openqa_hostname'] == 'somehost'

    # check arches is handled properly
    fakerun.reset_mock()
    # set up a custom WANTED with multiple arches that are present in
    # our mock data
    wanted = [
        {
            "match": {
                "subvariant": "Server",
                "type": "boot",
                "format": "iso",
                "arch": "x86_64",
            },
            "score": 6,
        },
        {
            "match": {
                "subvariant": "Server",
                "type": "boot",
                "format": "iso",
                "arch": "ppc64le",
            },
            "score": 6,
        },
        {
            "match": {
                "subvariant": "Minimal",
                "type": "raw-xz",
                "format": "raw.xz",
                "arch": "aarch64",
            },
        },
    ]
    # first check we get 8 runs (one for each image, x86_64 and
    # aarch64 upgrade flavors, three universal runs) with no arches
    # set by config or arg, and this WANTED. Note this includes the
    # ppc64le universal flavor, which may be a surprising result as
    # no ppc64le images are listed, but if you really want to never
    # schedule jobs for an arch, you should set that in
    # schedule.conf
    schedule.CONFIG.set("schedule", "arches", "")
    ret = schedule.jobs_from_compose(COMPURL, wanted=wanted)
    assert fakerun.call_count == 8
    # now check we get only 4 (one for each image, aarch64 upgrade,
    # and universal for both arches) if we limit the arches
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(COMPURL, wanted=wanted, arches=['ppc64le', 'aarch64'])
    assert fakerun.call_count == 5
    # also if we get an arch setting from config file
    schedule.CONFIG.set("schedule", "arches", "ppc64le,aarch64")
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(COMPURL, wanted=wanted)
    assert fakerun.call_count == 5

    # check flavors is handled properly, with all arches in play
    schedule.CONFIG.set("schedule", "arches", "")
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(COMPURL, flavors=['server-boot-iso', 'workstation-live-iso', 'foobar'])
    # server-boot-iso is wanted for x86_64, ppc64le, and aarch64
    # workstation-live-iso is wanted for x86_64 and ppc64le
    # foobar doesn't exist, universal SHOULD NOT be scheduled:
    # total == 5
    assert fakerun.call_count == 5

    # set config setting back to default
    schedule.CONFIG.set("schedule", "arches", "x86_64")

    # check flavors *and* arches is handled properly
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(COMPURL, flavors=['server-boot-iso', 'workstation-live-iso'], arches=['x86_64'])
    # we have one x86_64 image for each flavor, so 2
    assert fakerun.call_count == 2

    # check flavors with 'universal' is handled properly
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(
        COMPURL,
        flavors=['server-boot-iso', 'workstation-live-iso', 'universal'], arches=['x86_64']
    )
    # we have one x86_64 image for each flavor, and universal makes 3
    assert fakerun.call_count == 3
    # universal should use no ISO
    univ = [argtup[0][0] for argtup in fakerun.call_args_list if argtup[0][1] == 'universal'][0]
    assert "ISO_URL" not in univ

    # check *only* 'universal' is handled properly
    fakerun.reset_mock()
    ret = schedule.jobs_from_compose(COMPURL, flavors=['universal'], arches=['x86_64'])
    # we should only schedule 'universal', using the best candidate
    assert fakerun.call_count == 1
    # should use Server DVD ISO
    assert "ISO_URL" not in fakerun.call_args[0][0]

    # check we don't schedule upgrade flavors for releases that don't
    # have an https_url_generic
    fakerun.reset_mock()
    with mock.patch.object(fedfind.release.RawhideNightly, 'https_url_generic', None):
        ret = schedule.jobs_from_compose(COMPURL)
        # 7 images but *not* the upgrade flavors (inc. universal)
        assert fakerun.call_count == 7

    # check triggerexception is raised when appropriate
    with mock.patch('fedfind.release.get_release', side_effect=ValueError("Oops!")):
        with pytest.raises(schedule.TriggerException):
            ret = schedule.jobs_from_compose(COMPURL)

    with mock.patch('fedora_openqa.schedule._get_images', return_value=[]):
        with pytest.raises(schedule.TriggerException):
            ret = schedule.jobs_from_compose(COMPURL)

@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
@mock.patch.object(fedfind.release.RawhideNightly, 'type', 'production')
def test_jobs_from_compose_tag(fakeclient, fakerun, ffmock02):
    """Check that we tag candidate composes as 'important'."""
    # reset this in case previous test failed partway through
    schedule.CONFIG.set("schedule", "arches", "x86_64")
    ret = schedule.jobs_from_compose(COMPURL)
    assert ret == ('Fedora-Rawhide-20230502.n.0', [1 for _ in range(9)])
    # find the args that openqa_request was last called with
    reqargs = fakeclient.return_value.openqa_request.call_args
    assert reqargs[0] == ('POST', 'groups/1/comments')
    assert reqargs[1]['params'] == {'text': 'tag:Fedora-Rawhide-20230502.n.0:important:candidate'}

@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
@mock.patch.object(fedfind.release.RawhideNightly, 'label', 'RC-1.5')
def test_jobs_from_compose_label(fakerun, ffmock02):
    """Check that we pass compose label through to run_openqa_jobs if
    if there is one.
    """
    ret = schedule.jobs_from_compose(COMPURL)
    assert ret == ('Fedora-Rawhide-20230502.n.0', [1 for _ in range(9)])
    assert fakerun.call_args[1]["label"] == "RC-1.5"

@mock.patch('fedora_openqa.schedule.run_openqa_jobs', return_value=[1], autospec=True)
def test_jobs_from_compose_unsupported(fakerun):
    """Check that we create no jobs for composes fedfind explicitly
    tells us it does not support (by raising UnsupportedComposeError).
    """
    # note: this is a contrived scenario ATM, as there *are* no real
    # composes fedfind considers unsupported, as of 2018-07 (updates
    # composes now contain images and should be tested). So we just
    # sort of invent an 'Atomic updates-testing' compose, which we
    # we happen to know fedfind will treat as unsupported. We mock out
    # run_openqa_jobs just to ensure no jobs are created if the call
    # somehow actually tries to create them.
    ret = schedule.jobs_from_compose('https://kojipkgs.fedoraproject.org/compose/updates/Fedora-Atomic-27-updates-testing-20180123.0/compose/')
    assert ret == ('', [])

@mock.patch('fedfind.helpers.get_current_stables', return_value=[24, 25])
@mock.patch('fedfind.helpers.get_current_release', return_value=25)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
def test_jobs_from_update(fakeclient, fakecurrr, fakecurrs):
    """Tests for jobs_from_update."""
    # many assertions below depend on the number of update flavors
    # we have; instead of changing them all every time we change
    # that, we update this constant
    allflavors = set()
    for flavlist in UPDATE_FLAVORS.values():
        allflavors.update(flavlist)
    numflavors = len(allflavors)
    # the OpenQA_Client instance mock
    fakeinst = fakeclient.return_value
    # for now, return no 'jobs' (for the dupe query), one 'id' (for
    # the post request)
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    # simple case, using release detection
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', updic=UPDATEJSON)
    # should get as many jobs (all with id 1 due to the mock return
    # value) as we have flavors
    assert ret == [1 for i in range(numflavors)]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # should be as many calls as we have flavors
    assert len(posts) == numflavors
    parmdicts = [call[1]["data"] for call in posts]
    # checking two lists of dicts are equivalent is rather tricky; I
    # don't think we can technically rely on the order always being
    # the same, and in Python 3, a list of dicts cannot be sorted.
    # So we assert the length of the list, and assert that each of the
    # expected dicts is in the actual list.
    assert len(parmdicts) == numflavors
    advisories1 = ' '.join(UPDATENVRS_1)
    advisories2 = ' '.join(UPDATENVRS_2)
    checkdicts = [
        {
            'DISTRI': 'fedora',
            'VERSION': '25',
            'ARCH': 'x86_64',
            'BUILD': 'Update-FEDORA-2017-b07d628952',
            'ADVISORY': 'FEDORA-2017-b07d628952',
            'ADVISORY_NVRS_1': advisories1,
            'ADVISORY_NVRS_2': advisories2,
            'ADVISORY_OR_TASK': 'FEDORA-2017-b07d628952',
            'UPDATE_OR_TAG_REPO': 'nfs://172.16.2.110:/mnt/updateiso/update_repo',
            '_OBSOLETE': '1',
            '_ONLY_OBSOLETE_SAME_BUILD': '1',
            'START_AFTER_TEST': '',
            'QEMU_HOST_IP': '172.16.2.2',
            'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24',
            'FLAVOR': flavor,
            'CURRREL': '25',
            'RAWREL': '26',
            'UP1REL': '24',
            'UP2REL': '23',
        } for flavor in [f"updates-{oflav}" for oflav in allflavors]
    ]
    for checkdict in checkdicts:
        assert checkdict in parmdicts

    # test we do schedule jobs for the Rawhide release. Note:
    # fakecurrr returns 25 as the 'branched release' so code thinks
    # 'rawhide release' is 26
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='26', updic=UPDATEJSON)
    assert ret == [1 for i in range(numflavors)]
    # check we got all the posts and set version to the number
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # should be as many calls as we have flavors
    assert len(posts) == numflavors
    parmdicts = [call[1]["data"] for call in posts]
    for parmdict in parmdicts:
        assert parmdict["VERSION"] == "26"

    # check we don't crash or fail to schedule if get_current_release
    # or get_current_stables fail
    fakeinst.openqa_request.reset_mock()
    fakecurrs.side_effect = ValueError("Well, that was unfortunate")
    fakecurrr.side_effect = ValueError("Well, that was unfortunate")
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='26', updic=UPDATEJSON)
    assert ret == [1 for i in range(numflavors)]
    fakecurrs.side_effect = None

    # check we don't schedule upgrade jobs when update is for oldest
    # stable release
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='24', updic=UPDATEJSON)
    # upgrade flavors skipped, so numflavors - 2 jobs (there are two
    # upgrade flavors)
    assert ret == [1 for i in range(numflavors - 2)]

    # test 'flavors'
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='25', flavors=['server'], updic=UPDATEJSON)
    # should get one job
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    # check parm dict FLAVOR value
    assert posts[0][1]["data"]['FLAVOR'] == 'updates-server'

    # test dupe detection and 'force'
    fakeinst.openqa_request.reset_mock()
    # this looks like a 'dupe' for all flavors except workstation
    fakeinst.openqa_request.return_value = {
        'jobs': [
            {
                'settings': {
                    'FLAVOR': 'updates-container',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-server',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-everything-boot-iso',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-kde-live-iso',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-workstation-live-iso',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-kde',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-server-upgrade',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-workstation-upgrade',
                },
            },
            {
                'settings': {
                    'FLAVOR': 'updates-silverblue-dvd_ostree-iso',
                },
            },
        ],
        'ids': [1],
    }
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='25', updic=UPDATEJSON)
    # should get one job, for workstation (the only flavor we don't
    # have a 'dupe' for)
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    # check parm dict FLAVOR value
    assert posts[0][1]['data']['FLAVOR'] == 'updates-workstation'
    # now try with force=True
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='25', force=True, updic=UPDATEJSON)
    # should get numflavors jobs this time
    assert ret == [1 for i in range(numflavors)]

    # test extraparams
    fakeinst.openqa_request.reset_mock()
    # set the openqa_request return value back to the no-dupes version
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    # we intentionally test 'version' as a positional arg here to make
    # sure it isn't moved; it should never be moved as it was required
    # for a long time
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', '25', flavors=['server'], extraparams={'FOO': 'bar'},
                                    updic=UPDATEJSON)
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # check parm dict values
    assert posts[0][1]['data']['BUILD'] == 'Update-FEDORA-2017-b07d628952-EXTRA'
    assert posts[0][1]['data']['FOO'] == 'bar'

    # test openqa_hostname
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='25', openqa_hostname='openqa.example',
                                    updic=UPDATEJSON)
    assert fakeclient.call_args[0][0] == 'openqa.example'

    # test arch
    fakeinst.openqa_request.reset_mock()
    ret = schedule.jobs_from_update('FEDORA-2017-b07d628952', version='25', arch='ppc64le', updic=UPDATEJSON)
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # check parm dict values. They should have correct arch, if they
    # have HDD_1, it should be one of the expected values
    for post in posts:
        assert post[1]['data']['ARCH'] == 'ppc64le'
        if 'HDD_1' in post[1]['data']:
            assert post[1]['data']['HDD_1'] in ['disk_f25_server_3_ppc64le.qcow2',
                                           'disk_f25_desktop_4_ppc64le.qcow2',
                                           'disk_f25_kde_4_ppc64le.qcow2']

@mock.patch('fedfind.helpers.get_current_stables', return_value=[28, 29])
@mock.patch('fedfind.helpers.get_current_release', return_value=29)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
def test_jobs_from_update_kojitask(fakeclient, fakecurrr, fakecurrs):
    """Test jobs_from_update works as expected when passed a Koji task
    ID. We don't need to recheck everything, just the differing vars.
    """
    # the OpenQA_Client instance mock
    fakeinst = fakeclient.return_value
    # for now, return no 'jobs' (for the dupe query), one 'id' (for
    # the post request)
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    # simple case
    ret = schedule.jobs_from_update('32099714', version='28', flavors=['everything-boot-iso'])
    # should get one job for one flavor
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    parmdict = posts[0][1]["data"]
    assert parmdict == {
        'DISTRI': 'fedora',
        'VERSION': '28',
        'ARCH': 'x86_64',
        'BUILD': 'Kojitask-32099714-NOREPORT',
        'KOJITASK': '32099714',
        'ADVISORY_OR_TASK': '32099714',
        'UPDATE_OR_TAG_REPO': 'nfs://172.16.2.110:/mnt/updateiso/update_repo',
        '_OBSOLETE': '1',
        '_ONLY_OBSOLETE_SAME_BUILD': '1',
        'START_AFTER_TEST': '',
        'QEMU_HOST_IP': '172.16.2.2',
        'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24',
        'FLAVOR': 'updates-everything-boot-iso',
        'CURRREL': '29',
        'RAWREL': '30',
        'UP1REL': '27',
        'UP2REL': '26',
    }
    # multiple task case
    fakeinst.reset_mock()
    ret = schedule.jobs_from_update(['32099714', '32099715'], version='28', flavors=['everything-boot-iso'])
    # should get one job for one flavor
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    parmdict = posts[0][1]["data"]
    assert parmdict["KOJITASK"] == "32099714_32099715"
    assert parmdict["ADVISORY_OR_TASK"] == "32099714_32099715"
    assert parmdict["BUILD"] == "Kojitask-32099714_32099715-NOREPORT"
    # check we error out if no release is passed
    with pytest.raises(schedule.TriggerException):
        ret = schedule.jobs_from_update('32099714', flavors=['everything-boot-iso'])
    # check we error out if we try to pass non-task IDs in a list
    with pytest.raises(schedule.TriggerException):
        ret = schedule.jobs_from_update(
            ['32099714', 'FEDORA-2017-b07d628952'],
            version='28',
            flavors=['everything-boot-iso']
        )

@mock.patch('fedfind.helpers.get_current_stables', return_value=[28, 29])
@mock.patch('fedfind.helpers.get_current_release', return_value=29)
@mock.patch('fedora_openqa.schedule.OpenQA_Client', autospec=True)
def test_jobs_from_update_kojitag(fakeclient, fakecurrr, fakecurrs):
    """Test jobs_from_update works as expected when passed a Koji tag
    name. We don't need to recheck everything, just the differing vars.
    """
    # the OpenQA_Client instance mock
    fakeinst = fakeclient.return_value
    # for now, return no 'jobs' (for the dupe query), one 'id' (for
    # the post request)
    fakeinst.openqa_request.return_value = {'jobs': [], 'ids': [1]}
    # simple case
    ret = schedule.jobs_from_update('TAG_f39-python', version='28', flavors=['everything-boot-iso'])
    # should get one job for one flavor
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == 'POST']
    # one flavor, one call
    assert len(posts) == 1
    parmdict = posts[0][1]["data"]
    assert parmdict == {
        'DISTRI': 'fedora',
        'VERSION': '28',
        'ARCH': 'x86_64',
        'BUILD': 'TAG_f39-python-NOREPORT',
        'TAG': 'f39-python',
        'ADVISORY_OR_TASK': 'f39-python',
        'UPDATE_OR_TAG_REPO': 'https://kojipkgs.fedoraproject.org/repos/f39-python/latest/x86_64',
        '_OBSOLETE': '1',
        '_ONLY_OBSOLETE_SAME_BUILD': '1',
        'START_AFTER_TEST': '',
        'QEMU_HOST_IP': '172.16.2.2',
        'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24',
        'FLAVOR': 'updates-everything-boot-iso',
        'CURRREL': '29',
        'RAWREL': '30',
        'UP1REL': '27',
        'UP2REL': '26',
    }
    # check we error out if no release is passed
    with pytest.raises(schedule.TriggerException):
        ret = schedule.jobs_from_update('TAG_f39-python', flavors=['everything-boot-iso'])

@mock.patch("fedfind.helpers.download_json", return_value=COREOSJSON)
@mock.patch("fedfind.helpers.get_current_stables", return_value=[33, 34, 35])
@mock.patch("fedfind.helpers.get_current_release", return_value=35)
@mock.patch("fedora_openqa.schedule.OpenQA_Client", autospec=True)
def test_jobs_from_fcosbuild(fakeclient, fakecurrr, fakecurrs, fakejson):
    """Test scheduling jobs from a Fedora CoreOS build."""
    # the OpenQA_Client instance mock
    fakeinst = fakeclient.return_value
    # for now, return no 'jobs' (for the dupe query), one 'id' (for
    # the post request)
    fakeinst.openqa_request.return_value = {"jobs": [], "ids": [1]}
    # simple case, COREOSJSON is trimmed from the real meta.json here
    buildurl = "https://builds.coreos.fedoraproject.org/prod/streams/rawhide/builds/36.20211123.91.0/x86_64"
    ret = schedule.jobs_from_fcosbuild(buildurl)
    # should get one job back
    assert ret == [1]
    # find the POST calls
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == "POST"]
    # one flavor, one call
    assert len(posts) == 1
    parmdict = posts[0][0][2]
    assert parmdict == {
        "DISTRI": "fedora",
        "VERSION": "36",
        "ARCH": "x86_64",
        "BUILD": "Fedora-CoreOS-36.20211123.91.0",
        "_OBSOLETE": "1",
        "_ONLY_OBSOLETE_SAME_BUILD": "1",
        "QEMU_HOST_IP": "172.16.2.2",
        "NICTYPE_USER_OPTIONS": "net=172.16.2.0/24",
        "FLAVOR": "CoreOS-colive-iso",
        "CURRREL": "35",
        "RAWREL": "36",
        "UP1REL": "35",
        "UP2REL": "34",
        "IMAGETYPE": "colive",
        "ISO_URL": f"{buildurl}/fedora-coreos-36.20211123.91.0-live.x86_64.iso",
        "LOCATION": "",
        "SUBVARIANT": "CoreOS",
    }

    # test we get no jobs if we specify a non-found flavor
    ret = schedule.jobs_from_fcosbuild(buildurl, flavors=["nonexistent"])
    assert ret == []
    posts = [call for call in fakeinst.openqa_request.call_args_list if call[0][0] == "POST"]
    # should still only have one call
    assert len(posts) == 1


# vim: set textwidth=120 ts=8 et sw=4:
