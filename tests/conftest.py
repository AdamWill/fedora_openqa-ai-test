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

"""Test configuration and fixtures."""

from __future__ import unicode_literals
from __future__ import print_function

# stdlib imports
import json
import os
from unittest import mock

# external imports
import fedfind.release
import pytest


COMPURL = "https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170207.n.0/compose/"

@pytest.fixture(scope="function")
def jobdict01():
    """An openQA job dict, for a compose test."""
    return {
        "children": {
            "Chained": [],
            "Parallel": []
        },
        "clone_id": None,
        "group": "fedora",
        "group_id": 1,
        "id": 70581,
        "modules": [
            {
                "category": "tests",
                "flags": ["fatal"],
                "name": "_boot_to_anaconda",
                "result": "passed"
            },
            {
                "category": "tests",
                "flags": ["fatal", "milestone"],
                "name": "_console_wait_login",
                "result": "passed"
            },
            {
                "category": "tests",
                "flags": ["fatal"],
                "name": "freeipa_client",
                "result": "passed"
            }
        ],
        "name": "fedora-Rawhide-Server-dvd-iso-x86_64-BuildFedora-Rawhide-20170207.n.0-realmd_join_kickstart@64bit",
        "parents": {
            "Chained": [70579],
            "Parallel": [70577]
        },
        "priority": 40,
        "result": "passed",
        "retry_avbl": 3,
        "settings": {
            "ARCH": "x86_64",
            "BACKEND": "qemu",
            "BOOTFROM": "c",
            "BUILD": "Fedora-Rawhide-20170207.n.0",
            "CURRREL": "25",
            "DISTRI": "fedora",
            "FLAVOR": "Server-dvd-iso",
            "GRUB_POSTINSTALL": "net.ifnames=0 biosdevname=0",
            "HDD_1": "disk_64bit_cockpit.qcow2",
            "IMAGETYPE": "dvd",
            "ISO": "Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
            "ISO_URL": COMPURL + "Server/x86_64/iso/Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
            "LOCATION": COMPURL,
            "MACHINE": "64bit",
            # pylint: disable=line-too-long
            "NAME": "00070581-fedora-Rawhide-Server-dvd-iso-x86_64-BuildFedora-Rawhide-20170207.n.0-realmd_join_cockpit@64bit",
            "NICTYPE": "tap",
            "PARALLEL_WITH": "server_role_deploy_domain_controller",
            "PART_TABLE_TYPE": "mbr",
            "POSTINSTALL": "realmd_join_cockpit freeipa_webui freeipa_password_change freeipa_client",
            "QEMUCPU": "Nehalem",
            "QEMUCPUS": "2",
            "QEMURAM": "2048",
            "QEMUVGA": "qxl",
            "ROOT_PASSWORD": "weakpassword",
            "START_AFTER_TEST": "server_cockpit_default",
            "SUBVARIANT": "Server",
            "TEST": "server_realmd_join_kickstart",
            "TEST_TARGET": "ISO",
            "USER_LOGIN": "false",
            "VERSION": "Rawhide",
            "WORKER_CLASS": "tap"
        },
        "state": "done",
        "t_finished": "2017-02-01T11:57:32",
        "t_started": None,
        "test": "server_realmd_join_kickstart"
    }

@pytest.fixture(scope="function")
def jobdict02():
    """Another openQA job dict, this one for an update test."""
    return {
        "assets": {
            "hdd": ["disk_f25_server_3_x86_64.img"]
        },
        "assigned_worker_id": 8,
        "children": {
            "Chained": [],
            "Parallel": []
        },
        "clone_id": None,
        "group": "fedora",
        "group_id": 1,
        "id": 72517,
        "modules": [
            {
                "category": "tests",
                "flags": ["fatal", "milestone"],
                "name": "_console_wait_login",
                "result": "passed"
            },
            {
                "category": "tests",
                "flags": ["fatal"],
                "name": "_advisory_update",
                "result": "passed"
            }
            ,
            {
                "category": "tests",
                "flags": ["fatal"],
                "name": "base_selinux",
                "result": "passed"
            },
            {
                "category": "tests",
                "flags": ["fatal"],
                "name": "_advisory_post",
                "result": "passed"
            }
        ],
        "name": "fedora-25-updates-server-x86_64-BuildFEDORA-2017-376ae2b92c-base_selinux@64bit",
        "parents": {
            "Chained": [],
            "Parallel":[]
        },
        "priority": 40,
        "result": "passed",
        "retry_avbl": 3,
        "settings": {
            "ADVISORY": "FEDORA-2017-376ae2b92c",
            "ADVISORY_OR_TASK": "FEDORA-2017-376ae2b92c",
            "ARCH": "x86_64",
            "BACKEND": "qemu",
            "BOOTFROM": "c",
            "BUILD": "FEDORA-2017-376ae2b92c",
            "CURRREL": "25",
            "DISTRI": "fedora",
            "FLAVOR": "updates-server",
            "HDD_1": "disk_f25_server_3_x86_64.img",
            "MACHINE": "64bit",
            "NAME": "00072517-fedora-25-updates-server-x86_64-BuildFEDORA-2017-376ae2b92c-base_selinux@64bit",
            "PART_TABLE_TYPE": "mbr",
            "POSTINSTALL": "base_selinux",
            "QEMUCPU": "Nehalem",
            "QEMUCPUS": "2",
            "QEMURAM": "2048",
            "QEMUVGA": "qxl",
            "ROOT_PASSWORD": "weakpassword",
            "START_AFTER_TEST": "install_default_upload",
            "TEST": "base_selinux",
            "USER_LOGIN": "false",
            "VERSION": "25"
        },
        "state": "done",
        "t_finished": "2017-02-22T23:13:13",
        "t_started": "2017-02-22T23:07:29",
        "test": "base_selinux"
    }

@pytest.fixture(scope="function")
def jobdict03():
    """Another openQA job dict, for an IoT compose test."""
    return {
        "assets": {
            "hdd": [
                "00597768-disk_IoT-dvd_ostree-iso_64bit.qcow2"
            ],
            "iso": [
                "Fedora-IoT-IoT-ostree-x86_64-33-20200513.0.iso"
            ]
        },
        "assigned_worker_id": 38,
        "blocked_by_id": None,
        "children": {
            "Chained": [],
            "Directly chained": [],
            "Parallel": []
        },
        "clone_id": None,
        "group": "fedora",
        "group_id": 1,
        "id": 597773,
        "modules": [
            {
                "category": "fedora/tests",
                "flags": [
                    "important",
                    "fatal",
                    "milestone"
                ],
                "name": "_console_wait_login",
                "result": "passed"
            },
            {
                "category": "fedora/tests",
                "flags": [
                    "important",
                    "fatal"
                ],
                "name": "base_selinux",
                "result": "passed"
            }
        ],
        "name": "fedora-33-IoT-dvd_ostree-iso-x86_64-BuildFedora-IoT-33-20200513.0-base_selinux@64bit",
        "parents": {
            "Chained": [
                597768
            ],
            "Directly chained": [],
            "Parallel": []
        },
        "priority": 40,
        "result": "passed",
        "settings": {
            "ARCH": "x86_64",
            "ARCH_BASE_MACHINE": "64bit",
            "BACKEND": "qemu",
            "BOOTFROM": "c",
            "BUILD": "Fedora-IoT-33-20200513.0",
            "CANNED": "1",
            "CURRREL": "32",
            "DISTRI": "fedora",
            "FLAVOR": "IoT-dvd_ostree-iso",
            "HDD_1": "disk_IoT-dvd_ostree-iso_64bit.qcow2",
            "IMAGETYPE": "dvd-ostree",
            "ISO": "Fedora-IoT-IoT-ostree-x86_64-33-20200513.0.iso",
            "ISO_URL": "https://kojipkgs.fedoraproject.org/compose/iot/Fedora-IoT-33-20200513.0/compose/IoT/x86_64/iso/Fedora-IoT-IoT-ostree-x86_64-33-20200513.0.iso",
            "LABEL": "RC-20200513.0",
            "LOCATION": "https://kojipkgs.fedoraproject.org/compose/iot/Fedora-IoT-33-20200513.0/compose",
            "MACHINE": "64bit",
            "NAME": "00597773-fedora-33-IoT-dvd_ostree-iso-x86_64-BuildFedora-IoT-33-20200513.0-base_selinux@64bit",
            "PACKAGE_SET": "default",
            "PART_TABLE_TYPE": "mbr",
            "POSTINSTALL": "base_selinux",
            "QEMUCPU": "Nehalem",
            "QEMUCPUS": "2",
            "QEMURAM": "2048",
            "QEMUVGA": "virtio",
            "QEMU_VIRTIO_RNG": "1",
            "RAWREL": "33",
            "ROOT_PASSWORD": "weakpassword",
            "START_AFTER_TEST": "install_default_upload",
            "SUBVARIANT": "IoT",
            "TEST": "base_selinux",
            "TEST_SUITE_NAME": "base_selinux",
            "TEST_TARGET": "ISO",
            "UP1REL": "32",
            "UP2REL": "31",
            "USER_LOGIN": "false",
            "VERSION": "33",
            "WORKER_CLASS": "qemu_x86_64"
        },
        "state": "done",
        "t_finished": "2020-05-14T02:50:46",
        "t_started": "2020-05-14T02:49:27",
        "test": "base_selinux"
    }

@pytest.fixture(scope="function")
def jobdict04():
    """Another openQA job dict, for a Fedora CoreOS build test."""
    return {
        "assets": {
            "hdd": [
                "00048191-disk_CoreOS-colive-iso_64bit.qcow2"
            ],
            "iso": [
                "fedora-coreos-32.20200726.3.1-live.x86_64.iso"
            ]
        },
        "assigned_worker_id": 4,
        "blocked_by_id": None,
        "children": {
            "Chained": [],
            "Directly chained": [],
            "Parallel": []
        },
        "clone_id": None,
        "group": "fedora",
        "group_id": 1,
        "id": 48192,
        "modules": [
            {
                "category": "fedora/tests",
                "flags": [
                    "important",
                    "fatal",
                    "milestone"
                ],
                "name": "_console_wait_login",
                "result": "passed"
            },
            {
                "category": "fedora/tests",
                "flags": [
                    "important",
                    "fatal"
                ],
                "name": "base_services_start",
                "result": "passed"
            }
        ],
        "name": "fedora-32-CoreOS-colive-iso-x86_64-BuildFedora-CoreOS-32-20200726.3.1-base_services_start@64bit",
        "parents": {
            "Chained": [
                48191
            ],
            "Directly chained": [],
            "Parallel": []
        },
        "priority": 40,
        "result": "passed",
        "settings": {
            "ARCH": "x86_64",
            "ARCH_BASE_MACHINE": "64bit",
            "BACKEND": "qemu",
            "BOOTFROM": "c",
            "BUILD": "Fedora-CoreOS-32-20200726.3.1",
            "CANNED": "1",
            "DISTRI": "fedora",
            "FLAVOR": "CoreOS-colive-iso",
            "HDD_1": "disk_CoreOS-colive-iso_64bit.qcow2",
            "IMAGETYPE": "colive",
            "ISO": "fedora-coreos-32.20200726.3.1-live.x86_64.iso",
            "LOCATION": "https://kojipkgs.fedoraproject.org/compose/cloud/Fedora-Cloud-32-20200819.0/compose",
            "MACHINE": "64bit",
            # pylint: disable=line-too-long
            "NAME": "00048192-fedora-32-CoreOS-colive-iso-x86_64-BuildFedora-CoreOS-32-20200726.3.1-base_services_start@64bit",
            "NICTYPE_USER_OPTIONS": "net=172.16.2.0/24",
            "PART_TABLE_TYPE": "mbr",
            "POSTINSTALL": "base_services_start",
            "QEMUCPU": "Nehalem",
            "QEMUCPUS": "2",
            "QEMURAM": "2048",
            "QEMUVGA": "virtio",
            "QEMU_HOST_IP": "172.16.2.2",
            "QEMU_VIRTIO_RNG": "1",
            "ROOT_PASSWORD": "weakpassword",
            "START_AFTER_TEST": "install_default_upload",
            "SUBVARIANT": "CoreOS",
            "TEST": "base_services_start",
            "TEST_SUITE_NAME": "base_services_start",
            "TEST_TARGET": "ISO",
            "USER_LOGIN": "false",
            "VERSION": "32",
            "WORKER_CLASS": "qemu_x86_64"
        },
        "state": "done",
        "t_finished": "2020-08-21T23:48:23",
        "t_started": "2020-08-21T23:47:22",
        "test": "base_services_start"
    }

@pytest.fixture(scope="function")
def jobdict05():
    """Another jobdict, for a special case (install_default_upload on
    Workstation). Trimmed a bit for length.
    """
    return {
        "result": "passed",
        "settings": {
            "ARCH": "x86_64",
            "ARCH_BASE_MACHINE": "64bit",
            "BACKEND": "qemu",
            "BUILD": "Fedora-Rawhide-20220906.n.0",
            "CURRREL": "36",
            "DEPLOY_UPLOAD_TEST": "install_default_upload",
            "DESKTOP": "gnome",
            "DISTRI": "fedora",
            "FLAVOR": "Workstation-live-iso",
            "HDDSIZEGB": "20",
            "IMAGETYPE": "live",
            "ISO": "Fedora-Workstation-Live-x86_64-Rawhide-20220906.n.0.iso",
            "LIVE": "1",
            "LOCATION": "https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20220906.n.0/compose",
            "MACHINE": "64bit",
            "NICTYPE_USER_OPTIONS": "net=172.16.2.0/24",
            "PACKAGE_SET": "default",
            "PART_TABLE_TYPE": "mbr",
            "POSTINSTALL": "_collect_data",
            "QEMUCPU": "Nehalem",
            "QEMUCPUS": "2",
            "QEMURAM": "3072",
            "QEMUVGA": "virtio",
            "QEMU_HOST_IP": "172.16.2.2",
            "QEMU_VIRTIO_RNG": "1",
            "RAWREL": "38",
            "STORE_HDD_1": "disk_Workstation-live-iso_64bit.qcow2",
            "SUBVARIANT": "Workstation",
            "TEST": "install_default_upload",
            "TEST_SUITE_NAME": "install_default_upload",
            "TEST_TARGET": "ISO",
            "UP1REL": "37",
            "UP2REL": "36",
            "VERSION": "Rawhide",
            "WORKER_CLASS": "qemu_x86_64"
        },
        "state": "done",
        "t_finished": "2022-09-06T10:04:05",
        "t_started": "2022-09-06T09:36:00",
        "test": "install_default_upload"
    }

@pytest.fixture(scope="function")
def jobdict06():
    """Another jobdict, for a Fedora ELN test.
    """
    return {
        "assets": {
            "iso": [
                "Fedora-ELN-20230619.1-x86_64-boot.iso"
            ]
        },
        "assigned_worker_id": 78,
        "blocked_by_id": None,
        "children": {
            "Chained": [],
            "Directly chained": [],
            "Parallel": []
        },
        "clone_id": None,
        "group": "fedora",
        "group_id": 1,
        "has_parents": 0,
        "id": 1982167,
        "modules": [
            {
                "category": "tests",
                "flags": [
                    "important",
                    "fatal"
                ],
                "name": "_boot_to_anaconda",
                "result": "passed"
            }
        ],
        "name": "fedora-ELN-BaseOS-boot-iso-x86_64-BuildFedora-ELN-20230619.1-install_default@uefi",
        "parents": {
            "Chained": [],
            "Directly chained": [],
            "Parallel": []
        },
        "parents_ok": 1,
        "priority": 50,
        "result": "passed",
        "settings": {
            "ARCH": "x86_64",
            "ARCH_BASE_MACHINE": "64bit",
            "BACKEND": "qemu",
            "BUILD": "Fedora-ELN-20230619.1",
            "CURRREL": "38",
            "DEPLOY_UPLOAD_TEST": "install_default_upload",
            "DISTRI": "fedora",
            "FLAVOR": "BaseOS-boot-iso",
            "IMAGETYPE": "boot",
            "ISO": "Fedora-ELN-20230619.1-x86_64-boot.iso",
            "ISO_URL": "https://odcs.fedoraproject.org/composes/odcs-28282/compose/BaseOS/x86_64/iso/Fedora-ELN-20230619.1-x86_64-boot.iso",
            "LABEL": "Alpha-0.1687161601",
            "LOCATION": "https://odcs.fedoraproject.org/composes/odcs-28282/compose/",
            "MACHINE": "uefi",
            "NAME": "01982167-fedora-ELN-BaseOS-boot-iso-x86_64-BuildFedora-ELN-20230619.1-install_default@uefi",
            "NICTYPE_USER_OPTIONS": "net=172.16.2.0/24",
            "PACKAGE_SET": "default",
            "PART_TABLE_TYPE": "gpt",
            "POSTINSTALL": "_collect_data",
            "QEMUCPU": "Haswell",
            "QEMUCPUS": "2",
            "QEMURAM": "3072",
            "QEMU_HOST_IP": "172.16.2.2",
            "QEMU_MAX_MIGRATION_TIME": "480",
            "QEMU_VIDEO_DEVICE": "virtio-vga",
            "QEMU_VIRTIO_RNG": "1",
            "RAWREL": "39",
            "SUBVARIANT": "BaseOS",
            "TEST": "install_default",
            "TEST_SUITE_NAME": "install_default",
            "TEST_TARGET": "ISO",
            "UEFI": "1",
            "UEFI_PFLASH_CODE": "/usr/share/edk2/ovmf/OVMF_CODE.fd",
            "UEFI_PFLASH_VARS": "/usr/share/edk2/ovmf/OVMF_VARS.fd",
            "UP1REL": "38",
            "UP2REL": "37",
            "VERSION": "ELN",
            "WORKER_CLASS": "qemu_x86_64",
            "XRES": "1024",
            "YRES": "768"
        },
        "state": "done",
        "t_finished": "2023-06-19T16:54:22",
        "t_started": "2023-06-19T16:43:01",
        "test": "install_default"
    }


@pytest.fixture(scope="function")
def ffimg01():
    """A pre-canned fedfind image dict, for the x86_64 Server DVD from
    the 20170207.n.0 Rawhide nightly.
    """
    return {
        "variant": "Server",
        "arch": "x86_64",
        "bootable": True,
        "checksums": {
            "sha256": "a641656db6c2e26d97cf7697afbb1f0c510d37587b5fab5d2ce6bfbdedcc4449"
        },
        "disc_count": 1,
        "disc_number": 1,
        "format": "iso",
        "implant_md5": "1a9c27f768bb6c97562faaec4500f115",
        "mtime": 1486462254,
        "path": "Server/x86_64/iso/Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
        "size": 3001024512,
        "subvariant": "Server",
        "type": "dvd",
        # pylint: disable=line-too-long
        "url": "https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170207.n.0/compose/Server/x86_64/iso/Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
        # pylint: disable=line-too-long
        "direct_url": "https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170207.n.0/compose/Server/x86_64/iso/Fedora-Server-dvd-x86_64-Rawhide-20170207.n.0.iso",
        "volume_id": "Fedora-S-dvd-x86_64-rawh"
    }

@pytest.fixture(scope="function")
def ffimg02():
    """A pre-canned fedfind image dict, for the x86_64 BaseOS DVD from
    Fedora-ELN-20230619.1.
    """
    return {
        "variant": "BaseOS",
        "arch": "x86_64",
        "bootable": True,
        "checksums": {
            "sha256": "d87a353dc1c68b5d6cfd381f5e68738f4435499a579020c3bb328bd27ddde0e2"
        },
        "disc_count": 1,
        "disc_number": 1,
        "format": "iso",
        "implant_md5": "8351713601685df9bf5183792a9787ab",
        "mtime": 1687162748,
        "path": "BaseOS/x86_64/iso/Fedora-ELN-20230619.1-x86_64-boot.iso",
        "size": 774379520,
        "subvariant": "BaseOS",
        "type": "boot",
        # pylint: disable=line-too-long
        "url": "https://odcs.fedoraproject.org/composes/odcs-28282/compose/BaseOS/x86_64/iso/Fedora-ELN-20230619.1-x86_64-boot.iso",
        # pylint: disable=line-too-long
        "direct_url": "https://odcs.fedoraproject.org/composes/odcs-28282/compose/BaseOS/x86_64/iso/Fedora-ELN-20230619.1-x86_64-boot.iso",
        "volume_id": "Fedora-ELN-BaseOS-x86_64"
    }

@pytest.fixture(scope="function")
def ffmd01():
    """Incomplete metadata dict for fedfind mocking; provides enough
    data (on Rawhide 20170207.n.0 nightly) to avoid round trips for
    compose ID purposes.
    """
    return {
        "composeinfo": {
            "header": {
                "type": "productmd.composeinfo",
                "version": "1.2"
            },
            "payload": {
                "compose": {
                    "date": "20170207",
                    "id": "Fedora-Rawhide-20170207.n.0",
                    "respin": 0,
                    "type": "nightly"
                },
                "release": {
                    "internal": False,
                    "name": "Fedora",
                    "short": "Fedora",
                    "type": "ga",
                    "version": "Rawhide"
                },
            },
        },
    }

@pytest.fixture(scope="function")
def ffmd02():
    """Incomplete metadata dict for fedfind mocking; provides enough
    data (on Fedora-ELN-20230619.1) to avoid round trips for
    compose ID purposes.
    """
    return {
        "composeinfo": {
            "header": {
                "type": "productmd.composeinfo",
                "version": "1.2"
            },
            "payload": {
                "compose": {
                    "date": "20230619",
                    "id": "Fedora-ELN-20230619.1",
                    "respin": 1,
                    "type": "production"
                },
                "release": {
                    "internal": False,
                    "name": "Fedora",
                    "short": "Fedora",
                    "type": "ga",
                    "version": "ELN"
                },
            },
        },
    }

@pytest.yield_fixture(scope="function")
# pylint: disable=redefined-outer-name
def ffmock(ffmd01, ffmd02, ffimg01, ffimg02):
    """Mock up fedfind metadata and all_images using the ffmd01 and
    ffimg01/02 fixtures. Yield the current iteration of the dicts so
    the test can modify them if it wants.
    """
    mdpatch = mock.patch.object(fedfind.release.RawhideNightly, 'metadata', ffmd01)
    mdpatch2 = mock.patch.object(fedfind.release.ElnCompose, 'metadata', ffmd02)
    imgpatch = mock.patch.object(fedfind.release.RawhideNightly, 'all_images', [ffimg01])
    imgpatch2 = mock.patch.object(fedfind.release.ElnCompose, 'all_images', [ffimg02])
    mdpatch.start()
    mdpatch2.start()
    imgpatch.start()
    imgpatch2.start()
    yield (ffmd01, ffimg01)
    mdpatch.stop()
    mdpatch2.stop()
    imgpatch.stop()
    imgpatch2.stop()

@pytest.yield_fixture(scope="function")
def ffmock02():
    """Alternative fedfind mock using some real metadata files (from
    the Fedora-Rawhide-20230502.n.0 compose), for tests that need more
    complete metadata. The images.json is edited slightly to add
    toolbox images that were introduced since we started using this
    data (I just copied the dicts from a recent compose's images.json
    and changed the dates).
    """
    cifile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'composeinfo.json')
    with open(cifile, 'r') as cifh:
        cidict = json.loads(cifh.read())
    imgsfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'images.json')
    with open(imgsfile, 'r') as imgsfh:
        imgsdict = json.loads(imgsfh.read())
    metadata = {'composeinfo': cidict, 'images': imgsdict}
    mdpatch = mock.patch.object(fedfind.release.RawhideNightly, 'metadata', metadata)
    mdpatch.start()
    yield
    mdpatch.stop()

@pytest.yield_fixture(scope="function")
# pylint: disable=redefined-outer-name
def oqaclientmock(jobdict01):
    """Mock OpenQA_Client which has a specified base_url and always
    returns [jobdict01] from its get_jobs method. Yields the class
    mock, the instance mock, and the jobdict (so tests can modify it
    if they like).
    """
    patcher = mock.patch('fedora_openqa.report.OpenQA_Client', autospec=True)
    mockedoqa = patcher.start()
    # this is the MagicMock that will always be returned when a test
    # instantiates the class
    instance = mockedoqa.return_value
    instance.baseurl = 'https://some.url'
    # pylint doesn't get mock
    # pylint: disable=no-member
    instance.get_jobs.return_value = [jobdict01]
    yield (mockedoqa, instance, jobdict01)
    patcher.stop()

@pytest.yield_fixture(scope="function")
def wikimock():
    """Mock wikitcms Wiki which has a specific return value for
    report_validation_results. Yields the class mock and the
    instance mock.
    """
    patcher = mock.patch('fedora_openqa.report.Wiki', autospec=True)
    mockedwiki = patcher.start()
    # this is the MagicMock that will always be returned when a test
    # instantiates the class
    instance = mockedwiki.return_value
    instance.logged_in = True
    # pylint doesn't get mock
    # pylint: disable=no-member
    instance.report_validation_results.return_value = ([], [])
    yield (mockedwiki, instance)
    patcher.stop()

# vim: set textwidth=120 ts=8 et sw=4:
