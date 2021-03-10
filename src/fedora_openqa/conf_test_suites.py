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
    #   $RUNARCH$             - "i386", "x86_64", "arm"
    #   $BOOTMETHOD$          - "x86_64 BIOS", "x86_64 UEFI", "ARM", "aarch64"
    #   $FIRMWARE$            - "BIOS", "UEFI"
    #   $SUBVARIANT$          - productmd 'subvariant': "Server", "KDE"... "_Base" is stripped
    #   $SUBVARIANT_OR_LOCAL$ - productmd 'subvariant' as above, or "Local" when subvariant contains "Cloud"
    #   $CLOUD_OR_BASE$ -     - 'Cloud' when subvariant contains 'Cloud', 'Base' otherwise
    #   $IMAGETYPE$           - pungi 'type': "boot", "live"... "boot" -> "netinst"
    #   $FS$                  - filesystem: "ext3", "btrfs"... expected to be last element of openQA test name
    #   $DESKTOP$             - desktop: just the DESKTOP openQA setting

    "QA:Testcase_Mediakit_Repoclosure": {
        "env": "$SUBVARIANT$",
        "type": "Installation",
    },
    "QA:Testcase_Mediakit_FileConflicts": {
        "env": "$SUBVARIANT$",
        "type": "Installation",
    },
    "QA:Testcase_Boot_default_install": {
        "name": "$SUBVARIANT$_$IMAGETYPE$",
        "section": 'Default boot and install ($RUNARCH$)',
        "env": "VM $FIRMWARE$",
        "type": "Installation",
    },
    "QA:Testcase_arm_image_deployment": {
        "name": "$SUBVARIANT$",
        "section": "ARM disk images",
        "env": "$RUNARCH$ VM",
        "type": "Installation"
    },
    "QA:Testcase_install_to_VirtIO": {
        "section": "Storage devices",
        "env": "$RUNARCH$",
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
    "QA:Testcase_Anaconda_User_Interface_VNC": {
        "section": "User interface",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_User_Interface_VNC_Vncconnect": {
        "section": "User interface",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_User_Interface_serial_console": {
        "section": "User interface",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_user_creation": {
        "section": "Miscellaneous",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_install_to_PATA": {
        "section": "Storage devices",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_install_to_SATA": {
        "section": "Storage devices",
        "env": "$RUNARCH$",
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
        "env": "$RUNARCH$",
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
    "QA:Testcase_install_repository_HTTP_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_HTTP_variation": {
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
    "QA:Testcase_install_repository_NFSISO_variation": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_Hard_drive_variation": {
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
    "QA:Testcase_partitioning_custom_standard_partition_ext4": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_lvm_ext4": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_lvmthin": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_standard_partition_xfs": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_with_swap": {
        "section": "Custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_software_RAID": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_btrfs": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_btrfs_preserve_home": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_custom_btrfs_preserve_home": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_lvmthin": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_standard_partition_xfs": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_with_swap": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_lvm_ext4": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_blivet_standard_partition_ext4": {
        "section": "Advanced custom storage configuration",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_File_Path_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
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
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_workstation": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_workstation_encrypted": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_server": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_kde": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_current_any": {
        "section": "Upgrade",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_minimal": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_workstation": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_workstation_encrypted": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_server": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_dnf_previous_kde": {
        "section": "Upgrade",
        "env": "$RUNARCH$",
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
    "QA:Testcase_Arabic_Language_Install": {
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
    "QA:Testcase_Boot_Methods_Pxeboot": {
        "section": "PXE boot",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_rescue_mode": {
        "section": "Miscellaneous",
        "env": "$BOOTMETHOD$",
        "type": "Installation",
    },
    "QA:Testcase_base_initial_setup": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT$",
        "type": "Base",
    },
    "QA:Testcase_base_startup": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_reboot_unmount": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_system_logging": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_update_cli": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_edition_self_identification": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_services_start": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_selinux": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_base_service_manipulation": {
        "section": "$RUNARCH$",
        "env": "$SUBVARIANT_OR_LOCAL$",
        "type": "$CLOUD_OR_BASE$",
    },
    "QA:Testcase_kickstart_firewall_disabled": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_kickstart_firewall_configured": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_freeipa_trust_server_installation": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_freeipa_trust_server_uninstallation": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_freeipa_replication": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_postgresql_server_installation": {
        "env": "$RUNARCH$",
        "type": "Server",
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
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_Remote_Logging": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_upgrade_dnf_current_server_domain_controller": {
        "section": "Upgrade tests",
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_upgrade_dnf_previous_server_domain_controller": {
        "section": "Upgrade tests",
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_desktop_app_basic": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
        # FIXME: this is just hard-coded for now as we do not test
        # any other applications, but we should really use a sub to
        # derive this 'intelligently'
        "name": "terminal",
    },
    "QA:Testcase_desktop_browser": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_desktop_login": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_desktop_update_graphical": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_desktop_update_notification": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_desktop_error_checks": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_workstation_core_applications": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
    },
    "QA:Testcase_Printing_New_Printer": {
        "env": "$SUBVARIANT$",
        "type": "Desktop",
        "section": "$RUNARCH$",
        "name": "virtual printer",
    },
    "QA:Testcase_Server_firewall_default": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_Server_cockpit_default": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_Server_cockpit_basic": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_Server_filesystem_default": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_FreeIPA_web_ui": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_FreeIPA_password_change": {
        "env": "$RUNARCH$",
        "type": "Server",
    },
    "QA:Testcase_Modularity_module_list": {
        "section": "Modularity",
        "env": "Result",
        "type": "Base",
    },
    "QA:Testcase_Modularity_enable-disable_module": {
        "section": "Modularity",
        "env": "Result",
        "type": "Base",
    },
    "QA:Testcase_Modularity_install_module": {
        "section": "Modularity",
        "env": "Result",
        "type": "Base",
    },
    "QA:Testcase_Modularity_update_without_repos": {
        "section": "Modularity",
        "env": "Result",
        "type": "Base",
    },
    "QA:Testcase_Podman": {
        "env": "$RUNARCH$",
        # if we run this on anything but IoT, we may need to change this
        "type": "General",
    },
    "QA:Testcase_Greenboot": {
        "env": "$RUNARCH$",
        "type": "General",
    },
    "QA:Testcase_RpmOstree_Rebase": {
        "env": "$RUNARCH$",
        "type": "General",
    },
    "QA:Testcase_RpmOstree_Package_Layering": {
        "env": "$RUNARCH$",
        "type": "General",
    },
    "QA:Testcase_Clevis": {
        "env": "$RUNARCH$",
        "type": "General",
    },
    "QA:Testcase_Zezere_Ignition": {
        "env": "$RUNARCH$",
        "type": "General",
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
    # if each of the individual openQA test modules named in the
    # iterable were present in the openQA job and passed. e.g.:
    #
    # "testsuite_c": {
    #     "testcase_c": {"modules": ["module_1"],},
    # },
    #
    # The overall job result is *disregarded* in this case: so long as
    # all the listed modules passed, the test case is considered
    # passed. This handles test suites like realmd_join_cockpit, which
    # has an optional module that covers QA:Testcase_FreeIPA_web_ui ;
    # if that module passes we want to report a pass for that test
    # case, if that module fails we do *not* want to report a pass.
    "mediakit_repoclosure": [
        "QA:Testcase_Mediakit_Repoclosure",
    ],
    "mediakit_fileconflicts": [
        "QA:Testcase_Mediakit_FileConflicts",
    ],
    "install_default": [
        "QA:Testcase_Boot_default_install",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_base_startup",
    ],
    "install_default_upload": [
        "QA:Testcase_Boot_default_install",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_base_startup",
    ],
    "install_arm_image_deployment_upload": [
        "QA:Testcase_arm_image_deployment",
        "QA:Testcase_base_initial_setup",
        "QA:Testcase_base_startup",
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
        "QA:Testcase_install_repository_HTTP_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_http_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP_variation",
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
    "install_repository_nfsiso_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_NFSISO_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_repository_hd_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_Hard_drive_variation",
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
    "install_blivet_software_raid": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_software_RAID",
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
    "upgrade_minimal_uefi": [
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
    "upgrade_2_minimal_64bit": [
        "QA:Testcase_upgrade_dnf_previous_minimal",
        "QA:Testcase_upgrade_dnf_previous_any",
    ],
    "upgrade_2_minimal_uefi": [
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
    "upgrade_server_domain_controller": [
        "QA:Testcase_upgrade_dnf_current_server_domain_controller",
    ],
    "upgrade_realmd_client": [],
    "upgrade_2_server_domain_controller": [
        "QA:Testcase_upgrade_dnf_previous_server_domain_controller",
    ],
    "upgrade_2_realmd_client": [],
    "install_btrfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_btrfs",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_lvm_ext4": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_lvm_ext4",
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
    "install_standard_partition_ext4": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_standard_partition_ext4",
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
    "install_with_swap": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_with_swap",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_btrfs_preserve_home": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_custom_btrfs_preserve_home",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_btrfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_btrfs",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_btrfs_preserve_home": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_btrfs_preserve_home",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_btrfs_preserve_home_uefi": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_btrfs_preserve_home",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_lvmthin": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_lvmthin",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_lvm_ext4": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_lvm_ext4",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_standard_partition_ext4": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_standard_partition_ext4",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_blivet_with_swap": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_with_swap",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    # FIXME there isn't a test case for this yet, we added it to
    # openQA in response to F32 blocker bugs, we should probably add
    # a wiki test case too
    "install_blivet_resize_lvm": [],
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
    # FIXME there isn't a test case for this yet, we added it to
    # openQA in response to F32 blocker bugs, we should probably add
    # a wiki test case too
    "install_resize_lvm": [],
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
    "install_arabic_language": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        "QA:Testcase_Arabic_Language_Install",
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
    "install_blivet_xfs": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_blivet_standard_partition_xfs",
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
    "install_pxeboot": [
        "QA:Testcase_Boot_Methods_Pxeboot",
        "QA:Testcase_Kickstart_File_Path_Ks_Cfg",
    ],
    "base_selinux": [
        "QA:Testcase_base_selinux",
    ],
    "base_services_start": [
        "QA:Testcase_base_services_start",
    ],
    "base_service_manipulation": [
        "QA:Testcase_base_service_manipulation",
    ],
    "base_update_cli": [
        "QA:Testcase_base_update_cli",
    ],
    "base_reboot_unmount": [
        "QA:Testcase_base_reboot_unmount",
    ],
    "base_system_logging": [
        "QA:Testcase_base_system_logging",
    ],
    "release_identification": [
        "QA:Testcase_base_edition_self_identification",
    ],
    "install_kickstart_firewall_disabled": [
        "QA:Testcase_kickstart_firewall_disabled",
    ],
    "install_kickstart_firewall_configured": [
        "QA:Testcase_kickstart_firewall_configured",
    ],
    "install_vnc_server": [
        "QA:Testcase_Anaconda_User_Interface_VNC",
    ],
    # _server is the key test here: it will only pass if client
    # passes, and the wiki test is not passed unless both pass, so
    # no need to list anything for _client on its own
    "install_vnc_client": [],
    "install_vncconnect_server": [
        "QA:Testcase_Anaconda_User_Interface_VNC_Vncconnect",
    ],
    # _server is the key test here: it will only pass if client
    # passes, and the wiki test is not passed unless both pass, so
    # no need to list anything for _client on its own
    "install_vncconnect_client": [],
    "install_serial_console": [
        "QA:Testcase_Anaconda_User_Interface_serial_console",
    ],
    "server_role_deploy_domain_controller": [
        "QA:Testcase_freeipa_trust_server_installation",
        "QA:Testcase_freeipa_trust_server_uninstallation",
    ],
    "server_realmd_join_kickstart": [
        "QA:Testcase_realmd_join_kickstart",
        "QA:Testcase_FreeIPA_realmd_login",
        "QA:Testcase_domain_client_authenticate",
    ],
    "desktop_terminal": [
        "QA:Testcase_desktop_app_basic",
    ],
    "desktop_browser": [
        "QA:Testcase_desktop_browser",
    ],
    "desktop_login": [
        "QA:Testcase_desktop_login",
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
    "desktop_printing": [
        "QA:Testcase_Printing_New_Printer",
    ],
    # this does not fully satisfy QA:Testcase_base_artwork_release_identification
    # (not even together with release_identification), it only *partly*
    # covers it, so we cannot report any results from it
    "desktop_background": [],
    # this test is also a partial check for QA:Testcase_desktop_menus
    # but we cannot really mark that as passed if this passes as it
    # does not test *everything* required there
    "apps_startstop": {
        "QA:Testcase_workstation_core_applications": {
            "modules": ["workstation_core_applications"],
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
    # there isn't a wiki test case or release criterion that matches
    # this test
    "server_cockpit_updates": [
    ],
    "server_filesystem_default": [
        "QA:Testcase_Server_filesystem_default",
    ],
    "server_role_deploy_database_server": [
        "QA:Testcase_postgresql_server_installation",
    ],
    "server_database_client": [
        "QA:Testcase_database_server_remote_client",
    ],
    "server_remote_logging_server": [
        "QA:Testcase_Remote_Logging",
    ],
    # _server is the key test here: it will only pass if client
    # passes, and the wiki test is not passed unless both pass, so
    # no need to list anything for _client on its own
    "server_remote_logging_client": [],
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
    "server_freeipa_replication_master": {
        "QA:Testcase_freeipa_replication": {
            "testsuites": ["server_freeipa_replication_replica", "server_freeipa_replication_client"],
        }
    },
    "server_freeipa_replication_replica": {
        "QA:Testcase_freeipa_replication": {
            "testsuites": ["server_freeipa_replication_master", "server_freeipa_replication_client"],
        }
    },
    "server_freeipa_replication_client": {
        "QA:Testcase_freeipa_replication": {
            "testsuites": ["server_freeipa_replication_master", "server_freeipa_replication_replica"],
        }
    },
    "install_iscsi": [
        "QA:Testcase_install_to_iSCSI_no_authentication",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
    ],
    "install_no_user": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_base_initial_setup",
    ],
    "modularity_tests": [
        "QA:Testcase_Modularity_module_list",
        "QA:Testcase_Modularity_enable-disable_module",
        "QA:Testcase_Modularity_install_module",
        "QA:Testcase_Modularity_update_without_repos",
    ],
    "cloud_autocloud": [
        "QA:Testcase_base_startup",
        "QA:Testcase_base_system_logging",
        "QA:Testcase_base_services_start",
        "QA:Testcase_base_selinux",
        "QA:Testcase_base_service_manipulation",
    ],
    # we report the result on podman_client as it does the final
    # check
    "podman": [],
    "podman_client": [
        "QA:Testcase_Podman",
    ],
    "iot_greenboot": [
        "QA:Testcase_Greenboot",
    ],
    "iot_rpmostree_rebase": [
        "QA:Testcase_RpmOstree_Rebase",
    ],
    "iot_rpmostree_overlay": [
        "QA:Testcase_RpmOstree_Package_Layering",
    ],
    "iot_clevis": [
        "QA:Testcase_Clevis",
    ],
    # server is just support here
    "iot_zezere_server": [],
    "iot_zezere_ignition": [
        "QA:Testcase_Zezere_Ignition",
    ],
    # this is a support test for other tests
    "support_server": [],
    # this is a data test, does not map to any test case
    "memory_check": [],
    # this test is a partial check for QA:Testcase_desktop_menus but
    # we cannot really mark that as passed if this passes as it does
    # not test *everything* required there
}

# vim: set textwidth=120 ts=8 et sw=4:
