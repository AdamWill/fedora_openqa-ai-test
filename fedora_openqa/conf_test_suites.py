# Copyright (C) 2015 Red Hat
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
# Author(s): Jan Sedlak <jsedlak@redhat.com>
#            Josef Skladanka <jskladan@redhat.com>
#            Adam Williamson <awilliam@redhat.com>

"""This module contains data for mapping openQA jobs to Wikitcms test
instances.
"""

TESTCASES = {
    # the following strings in values will be replaced with strings
    # derived from openQA job settings, this is used for e.g. to get
    # the correct 'environment' or 'testname'.
    #
    #   special value       replacement
    #
    #   $RUNARCH$           - "i386", "x86_64"
    #   $BOOTMETHOD$        - "x86_64 BIOS", "x86_64 UEFI"
    #   $FIRMWARE$          - "BIOS", "UEFI"
    #   $SUBVARIANT$        - productmd 'subvariant': "Server", "KDE"... "_Base" is stripped
    #   $SUBVARIANT_OR_ARM$ - productmd 'subvariant' as above, or "ARM" when running on ARM architecture
    #   $IMAGETYPE$         - pungi 'type': "boot", "live"... "boot" -> "netinst"
    #   $FS$                - filesystem: "ext3", "btrfs"... expected to be last element of openQA test name
    #   $DESKTOP$           - desktop: just the DESKTOP openQA setting
    #   $ROLE$              - server role, for role_deploy_ tests: "domain_controller", "database_server"

    "QA:Testcase_Boot_default_install": {
        "name": "$SUBVARIANT$_$IMAGETYPE$",
        "section": 'Default boot and install ($RUNARCH$)',
        "env": "VM $FIRMWARE$",
        "type": "Installation",
    },
    "QA:Testcase_arm_image_deployment": {
        "name": "$SUBVARIANT$",
        "section": "ARM disk images",
        "env": "Ext boot",
        "type": "Installation"
    },
    "QA:Testcase_install_to_VirtIO": {
        "section": "Storage devices",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_empty": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_User_Interface_Graphical": {
        "section": "User interface",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_User_Interface_Text": {
        "section": "User interface",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_user_creation": {
        "section": "Miscellaneous",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_install_to_PATA": {
        "section": "Storage devices",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_install_to_SATA": {
        "section": "Storage devices",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_delete_all": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_multi_select": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_install_to_SCSI": {
        "section": "Storage devices",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_updates.img_via_URL": {
        "section": "Miscellaneous",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_kickstart_user_creation": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_Http_Server_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_Mirrorlist_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_HTTP/FTP_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_HTTP/FTP_variation": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_NFS_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_NFS_variation": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Package_Sets_Minimal_Package_Install": {
        "section": "Package sets",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_encrypted": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_delete_partial": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_free_space": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_multi_empty_all": {
        "section": "Guided storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_software_RAID": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_btrfs": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_lvmthin": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_standard_partition_ext3": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_standard_partition_xfs": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_no_swap": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_Hd_Device_Path_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_Nfs_Server_Path_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_minimal": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_workstation": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_workstation_encrypted": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_server": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_kde": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_any": {
        "section": "Upgrade",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_minimal": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_workstation": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_workstation_encrypted": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_server": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_kde": {
        "section": "Upgrade",
        "env": "x86_64",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_any": {
        "section": "Upgrade",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_updates.img_via_local_media": {
        "section": "Miscellaneous",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_shrink": {
        "section": "Guided storage shrinking",
        "env": "$FS$",
        "type": "Installation",
    },
    "QA:Testcase_Non-English_European_Language_Install": {
        "section": "Internationalization and Localization",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Package_Sets_KDE_Package_Install": {
        "section": "Package sets",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_to_iSCSI_no_authentication": {
        "section": "Storage devices",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_Cyrillic_Language_Install": {
        "section": "Internationalization and Localization",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Asian_Language_Install": {
        "section": "Internationalization and Localization",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_updates.img_via_installation_source": {
        "section": "Miscellaneous",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_rescue_mode": {
        "section": "Miscellaneous",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_base_initial_setup": {
        "env": "$SUBVARIANT_OR_ARM$",
        "type": "Base",
    },
    "QA:Testcase_base_selinux": {
        "env": "$SUBVARIANT$",
        "type": "Base",
    },
    "QA:Testcase_Services_start": {
        "env": "$SUBVARIANT_OR_ARM$",
        "type": "Base",
    },
    "QA:Testcase_base_service_manipulation": {
        "env": "$SUBVARIANT$",
        "type": "Base",
    },
    "QA:Testcase_base_update_cli": {
        "env": "$SUBVARIANT$",
        "type": "Base",
    },
    "QA:Testcase_kickstart_firewall_disabled": {
        "env": "x86",
        "type": "Server",
    },
    "QA:Testcase_kickstart_firewall_configured": {
        "env": "x86",
        "type": "Server",
    },
    "QA:Testcase_Server_role_deploy": {
        "env": "x86",
        "type": "Server",
        "name": "$ROLE$",
    },
    "QA:Testcase_realmd_join_kickstart": {
        # the section name here is pretty funky and I might change it,
        # so we'll intentionally use an inexact match
        "section": "FreeIPA",
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_realmd_join_cockpit": {
        "section": "FreeIPA",
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_realmd_join_sssd": {
        "section": "FreeIPA",
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_domain_client_authenticate": {
        "env": "Result",
        "type": "Server",
        "name": "(FreeIPA)",
    },
    "QA:Testcase_FreeIPA_realmd_login": {
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_database_server_remote_client": {
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_desktop_terminal": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "Release-blocking desktops: <b>x86 / x86_64</b>",
    },
    "QA:Testcase_desktop_browser": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "Release-blocking desktops: <b>x86 / x86_64</b>",
    },
    "QA:Testcase_desktop_update_graphical": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "Release-blocking desktops: <b>x86 / x86_64</b>",
    },
    "QA:Testcase_desktop_update_notification": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "Release-blocking desktops: <b>x86 / x86_64</b>",
    },
    "QA:Testcase_desktop_error_checks": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "Release-blocking desktops: <b>x86 / x86_64</b>",
    },
    "QA:Testcase_Server_firewall_default": {
        "env": "x86",
        "type": "Server",
    },
    "QA:Testcase_Server_cockpit_default": {
        "env": "x86",
        "type": "Server",
    },
    "QA:Testcase_Server_cockpit_basic": {
        "env": "x86",
        "type": "Server",
    },
    "QA:Testcase_FreeIPA_web_ui": {
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_FreeIPA_password_change": {
        "env": "Result",
        "type": "Server",
    },
    #        "": {
    #            "name": "", # optional, use when same testcase occurs on multiple rows with different link text
    #            "section": "", # optional, some result pages have no sections
    #            "env": "x86",
    #            "type": "Installation",
    #            },
}

# This is used to update TESTCASES dict for ResultsDB reporting
TESTCASES_RESULTSDB_EXTRADATA = {
    "QA:Testcase_partitioning_guided_shrink": {
        "filesystem": "$FS$",  # needed to convert test_fs to only one testcase
    },
}

TESTSUITES = {
    # each entry in this dict is named for an openQA test suite, and
    # represents the Wikitcms test cases that passed if that openQA
    # test suite passed or soft failed (from here on, read 'passed' to
    # mean 'passed or soft failed'). The value can either be a simple
    # list of test case names (each must be an entry in the TESTCASES
    # dict), or a dict.
    #
    # In the dict form, the dict's keys are the test case names, and
    # and the values must all be dicts. These dicts indicate extra
    # conditions that must be met before the test case will be counted
    # as 'passed'. An empty dict works just like the simple list case:
    # that test case will be considered 'passed' as long as the test
    # suite passed.
    #
    # The dict may contain a 'testsuites' key, whose value must be an
    # iterable. If so, the test case will only be considered 'passed'
    # if both the test suite being considered passed *and* all the
    # other test suites named in the iterable passed, for the same
    # build, machine and flavor. e.g.:
    #
    # "testsuite_a": {
    #     "testcase_a": {},
    #     "testcase_b": {"testsuites": ["testsuite_b"],},
    # },
    #
    # In this case, if testsuite_a passed, testcase_a would be counted
    # as passed, but testcase_b would only be counted as passed if
    # testsuite_b had also already passed. This covers cases like
    # desktop notifications, where there are two wiki test cases that
    # can be considered passed only if both desktop_notifications_live
    # and desktop_notifications_postinstall passed.
    #
    # NOTE: unless we can be sure one test suite will always run after
    # the other, we must include entries for *both* test suites,
    # because we will process the entry for whichever test suite
    # passes first and generate no 'pass' because the other one is not
    # done yet, then when the other one passes we will process its
    # entry and generate a pass so long as the first one also passed;
    # if we don't have entries for both test suites and the 'wrong
    # one' passes first, we will miss the result.
    #
    # The dict may contain a 'modules' key, whose value must be an
    # iterable. If so, the test case will only be considered 'passed'
    # if the overall openQA job passed *and* each of the individual
    # openQA test modules named in the iterable were present in the
    # openQA job and passed. e.g.:
    #
    # "testsuite_c": {
    #     "testcase_c": {"modules": ["module_1"],},
    # },
    #
    # In this case, testcase_c would only be considered 'passed' if
    # both testsuite_c passed *and* it contained a test module named
    # module_1 and that module passed. This handles test suites like
    # realmd_join_cockpit, which has an optional module that covers
    # QA:Testcase_FreeIPA_web_ui ; if that module passes we want to
    # report a pass for that test case, if the job passes but that
    # module fails we do *not* want to report a pass.
    "install_default": [
        "QA:Testcase_Boot_default_install",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
    ],
    "install_default_upload": [
        "QA:Testcase_Boot_default_install",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
    ],
    "install_arm_image_deployment_upload": [
        "QA:Testcase_arm_image_deployment",
        "QA:Testcase_base_initial_setup",
    ],
    "install_package_set_minimal": [
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_delete_pata": [
        "QA:Testcase_install_to_PATA",
        "QA:Testcase_partitioning_guided_delete_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_sata": [
        "QA:Testcase_install_to_SATA",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_multi": [
        "QA:Testcase_partitioning_guided_multi_select",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_scsi_updates_img": [
        "QA:Testcase_install_to_SCSI",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_updates.img_via_URL",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_kickstart_user_creation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Http_Server_Ks_Cfg",
    ],
    "install_mirrorlist_graphical": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_Mirrorlist_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_http_graphical": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_http_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_nfs_graphical": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_NFS_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_nfs_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_NFS_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_simple_encrypted": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
    ],
    "install_delete_partial": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_delete_partial",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_simple_free_space": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_free_space",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_multi_empty": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_multi_empty_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_software_raid": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_software_RAID",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_kickstart_hdd": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Hd_Device_Path_Ks_Cfg",
    ],
    "install_kickstart_nfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Nfs_Server_Path_Ks_Cfg",
    ],
    "upgrade_minimal_64bit": [
        "QA:Testcase_upgrade_dnf_current_minimal",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_desktop_64bit": [
        "QA:Testcase_upgrade_dnf_current_workstation",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_desktop_encrypted_64bit": [
        "QA:Testcase_upgrade_dnf_current_workstation_encrypted",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_server_64bit": [
        "QA:Testcase_upgrade_dnf_current_server",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_kde_64bit": [
        "QA:Testcase_upgrade_dnf_current_kde",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_desktop_32bit": [
        "QA:Testcase_upgrade_dnf_current_workstation",
        "QA:Testcase_upgrade_dnf_current_any",
    ],
    "upgrade_2_minimal_64bit": [
        "QA:Testcase_upgrade_dnf_previous_minimal",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_desktop_64bit": [
        "QA:Testcase_upgrade_dnf_previous_workstation",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_desktop_encrypted_64bit": [
        "QA:Testcase_upgrade_dnf_previous_workstation_encrypted",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_server_64bit": [
        "QA:Testcase_upgrade_dnf_previous_server",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_kde_64bit": [
        "QA:Testcase_upgrade_dnf_previous_kde",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_desktop_32bit": [
        "QA:Testcase_upgrade_dnf_previous_workstation",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "install_btrfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_btrfs",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_lvmthin": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_lvmthin",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_ext3": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_standard_partition_ext3",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_updates_img_local": [
        "QA:Testcase_Anaconda_updates.img_via_local_media",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_no_swap": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_no_swap",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_shrink_ext4": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_shrink",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_shrink_ntfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_shrink",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_european_language": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        "QA:Testcase_Non-English_European_Language_Install",
    ],
    "install_cyrillic_language": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        "QA:Testcase_Cyrillic_Language_Install",
    ],
    "install_asian_language": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        "QA:Testcase_Asian_Language_Install",
    ],
    "install_xfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_standard_partition_xfs",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_package_set_kde": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_KDE_Package_Install",
    ],
    "install_updates_nfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Anaconda_updates.img_via_installation_source",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_anaconda_text": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Text",
        "QA:Testcase_Anaconda_user_creation",
    ],
    "install_rescue_encrypted": [
        "QA:Testcase_Anaconda_rescue_mode",
    ],
    "base_selinux": [
        "QA:Testcase_base_selinux",
    ],
    "base_services_start": [
        "QA:Testcase_Services_start",
    ],
    "base_services_start_arm": [
        "QA:Testcase_Services_start",
    ],
    "base_service_manipulation": [
        "QA:Testcase_base_service_manipulation",
    ],
    "base_update_cli": [
        "QA:Testcase_base_update_cli",
    ],
    "install_kickstart_firewall_disabled": [
        "QA:Testcase_kickstart_firewall_disabled",
    ],
    "install_kickstart_firewall_configured": [
        "QA:Testcase_kickstart_firewall_configured",
    ],
    "server_role_deploy_domain_controller": [
        "QA:Testcase_Server_role_deploy",
    ],
    "server_realmd_join_kickstart": [
        "QA:Testcase_realmd_join_kickstart",
        "QA:Testcase_FreeIPA_realmd_login",
        "QA:Testcase_domain_client_authenticate",
    ],
    "desktop_terminal": [
        "QA:Testcase_desktop_terminal",
    ],
    "desktop_browser": [
        "QA:Testcase_desktop_browser",
    ],
    "desktop_update_graphical": [
        "QA:Testcase_desktop_update_graphical",
    ],
    "desktop_notifications_live": {
        "QA:Testcase_desktop_update_notification": {
            "testsuites": ["desktop_notifications_postinstall"],
        },
        "QA:Testcase_desktop_error_checks": {
            "testsuites": ["desktop_notifications_postinstall"],
        },
    },
    "desktop_notifications_postinstall": {
        "QA:Testcase_desktop_update_notification": {
            "testsuites": ["desktop_notifications_live"],
        },
        "QA:Testcase_desktop_error_checks": {
            "testsuites": ["desktop_notifications_live"],
        },
    },
    "server_firewall_default": [
        "QA:Testcase_Server_firewall_default",
    ],
    "server_cockpit_default": [
        "QA:Testcase_Server_cockpit_default",
    ],
    "server_cockpit_basic": [
        "QA:Testcase_Server_cockpit_basic",
    ],
    "server_role_deploy_database_server": [
        "QA:Testcase_Server_role_deploy",
    ],
    "server_database_client": [
        "QA:Testcase_database_server_remote_client",
    ],
    "realmd_join_cockpit": {
        "QA:Testcase_realmd_join_cockpit": {},
        "QA:Testcase_FreeIPA_realmd_login": {},
        "QA:Testcase_domain_client_authenticate": {},
        "QA:Testcase_FreeIPA_web_ui": {
            "modules": ["freeipa_webui"],
        },
        "QA:Testcase_FreeIPA_password_change": {
            "modules": ["freeipa_password_change"],
        },
    },
    "realmd_join_sssd": [
        "QA:Testcase_realmd_join_sssd",
        "QA:Testcase_FreeIPA_realmd_login",
        "QA:Testcase_domain_client_authenticate",
    ],
    "install_iscsi": [
        "QA:Testcase_install_to_iSCSI_no_authentication",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
}

# vim: set textwidth=120 ts=8 et sw=4:
