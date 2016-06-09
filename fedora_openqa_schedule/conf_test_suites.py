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
    #   $RUNARCH_OR_UEFI$   - "i386", "x86_64", or "UEFI" for x86_64 UEFI
    #   $RUNARCH$           - "i386", "x86_64"
    #   $BOOTMETHOD$        - "x86_64 BIOS", "x86_64 UEFI"
    #   $SUBVARIANT$        - productmd 'subvariant': "Server", "KDE"... "_Base" is stripped
    #   $SUBVARIANT_OR_ARM$ - productmd 'subvariant' as above, or "ARM" when running on ARM architecture
    #   $IMAGETYPE$         - pungi 'type': "boot", "live"... "boot" -> "netinst"
    #   $FS$                - filesystem: "ext3", "btrfs"... expected to be last element of openQA test name
    #   $DESKTOP$           - desktop: just the DESKTOP openQA setting

    "QA:Testcase_Boot_default_install": {
        "name": "$SUBVARIANT$_$IMAGETYPE$",
        "section": 'Default boot and install',
        "env": "$RUNARCH_OR_UEFI$",
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
    "QA:Testcase_Package_Sets_Minimal_Package_Install": {
        "section": "Package sets",
        "env": "$RUNARCH$",
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
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_install_to_iSCSI_no_authentication": {
        "section": "Storage devices",
        "env": "$RUNARCH$",
        "type": "Installation",
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
        # for now we're only testing this role, but we could easily
        # test Database server too and we'd need to tweak this somehow
        "name": "Domain controller",
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
    "QA:Testcase_domain_client_authenticate": {
        "env": "Result",
        "type": "Server",
        "name": "(FreeIPA)",
    },
    "QA:Testcase_FreeIPA_realmd_login": {
        "env": "Result",
        "type": "Server",
    },
    "QA:Testcase_desktop_terminal": {
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
    #        "": {
    #            "name": "", # optional, use when same testcase occurs on multiple rows with different link text
    #            "section": "", # optional, some result pages have no sections
    #            "env": "x86",
    #            "type": "Installation",
    #            },
}


TESTSUITES = {
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
    "install_mirrorlist_http_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
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
    "upgrade_minimal_64bit": [
        "QA:Testcase_upgrade_dnf_current_minimal",
        "QA:Testcase_upgrade_dnf_current_any",
        ],
    "upgrade_desktop_64bit": [
        "QA:Testcase_upgrade_dnf_current_workstation",
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
    "upgrade_minimal_32bit": [
        "QA:Testcase_upgrade_dnf_current_minimal",
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
    "upgrade_2_server_64bit": [
        "QA:Testcase_upgrade_dnf_previous_server",
        "QA:Testcase_upgrade_dnf_previous_any",
        ],
    "upgrade_2_kde_64bit": [
        "QA:Testcase_upgrade_dnf_previous_kde",
        "QA:Testcase_upgrade_dnf_previous_any",
        ],
    "upgrade_2_minimal_32bit": [
        "QA:Testcase_upgrade_dnf_previous_minimal",
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
    "server_firewall_default": [
        "QA:Testcase_Server_firewall_default",
        ],
    "server_cockpit_default": [
        "QA:Testcase_Server_cockpit_default",
        ],
    "server_cockpit_basic": [
        "QA:Testcase_Server_cockpit_basic",
        ],
    "realmd_join_cockpit": [
        "QA:Testcase_realmd_join_cockpit",
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
