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
# Author(s): Jan Sedlak <jsedlak@redhat.com>
#            Josef Skladanka <jskladan@redhat.com>
#            Adam Williamson <awilliam@redhat.com>

"""Scheduler module for fedora-openqa-schedule. Functions related to
job scheduling go here.
"""

# Standard libraries
import logging
import os.path

# External dependencies
try:
    # these are only in fedfind 4+
    from fedfind.exceptions import UnsupportedComposeError, UrlMatchError, CidMatchError
except ImportError:
    UnsupportedComposeError = UrlMatchError = CidMatchError = None
import fedfind.helpers
import fedfind.release
from openqa_client.client import OpenQA_Client
import openqa_client.exceptions

# Internal dependencies
from .config import WANTED, CONFIG, UPDATETL

logger = logging.getLogger(__name__)

FORMAT_TO_PARAM = {
    "iso": "ISO_URL",
    # let's connect it as second HDD - we can then use NUMDISKS=1 when we don't need it connected
    "raw.xz": "HDD_2_DECOMPRESS_URL",
    "qcow2": "HDD_2_URL",
}

# flavors to schedule update tests for; we put it here so the tests
# can import it. The keys here are critical path group names, the
# values are the flavors we need to schedule for updates in each
# critical path group. The associations here need to be kept in line
# with the greenwave gating policy at
# https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/greenwave/templates/fedora.yaml
# - for each group, we need to schedule all the flavors from which
# tests are listed in any gating policy that's applied to the decision
# context for that group. So as we gate on tests from every flavor for
# the 'core' and 'critical-path-base' groups, we need to schedule
# every flavor; as we only gate on tests from "kde" and "kde-live-iso"
# for the "critical-path-kde" group, we only need to schedule those
# flavors; and so on.
UPDATE_FLAVORS = {
    "core": (
        "container",
        "server",
        "server-upgrade",
        "kde",
        "kde-live-iso",
        "workstation",
        "workstation-upgrade",
        "workstation-live-iso",
        "everything-boot-iso",
        "silverblue-dvd_ostree-iso",
    ),
    "critical-path-anaconda": (
        "everything-boot-iso",
        "kde-live-iso",
        "silverblue-dvd_ostree-iso",
        "workstation-live-iso"
    ),
    "critical-path-apps": ("kde", "server", "workstation"),
    "critical-path-base": (
        "container",
        "server",
        "server-upgrade",
        "kde",
        "kde-live-iso",
        "workstation",
        "workstation-upgrade",
        "workstation-live-iso",
        "everything-boot-iso",
        "silverblue-dvd_ostree-iso",
    ),
    "critical-path-compose": (
        # podman and its deps are in this group
        "container",
        "everything-boot-iso",
        "kde-live-iso",
        "silverblue-dvd_ostree-iso",
        "workstation-live-iso"
    ),
    "critical-path-gnome": ("workstation", "workstation-upgrade", "workstation-live-iso", "silverblue-dvd_ostree-iso"),
    "critical-path-kde": ("kde", "kde-live-iso"),
    "critical-path-server": ("server", "server-upgrade"),
}


class TriggerException(Exception):
    pass


def _get_images(rel, wanted=None):
    """Given a fedfind Release instance, this returns a list of (flavor, arch, {param: url},
    subvariant, imagetype) tuples for images to be tested.
    """
    toolboxes = {
        img["arch"]: img["direct_url"] for img in rel.all_images
        if img["subvariant"] == "Container_Toolbox"
        and img["type"] == "docker"
        and img["format"] == "tar.xz"
    }
    if not wanted:
        wanted = WANTED
    images = []
    for wantimg in wanted:
        matchdict = wantimg['match'].copy()
        for foundimg in rel.all_images:
            # see if the foundimg matches the wantimg
            if not all(item in foundimg.items() for item in matchdict.items()):
                continue
            # assign a 'flavor' using fedfind's 'image identifier'
            flavor = fedfind.helpers.identify_image(foundimg, undersub=True, out='string')
            # get a couple of values we use for other reasons
            subvariant = foundimg['subvariant']
            imagetype = foundimg['type']
            arch = foundimg['arch']
            url = foundimg["direct_url"]
            logger.debug("Found image %s for arch %s at %s", flavor, arch, url)

            # some tests need more than one file, so let's collect them now
            param_urls = {
                FORMAT_TO_PARAM[foundimg['format']]: url
            }
            if arch in toolboxes:
                param_urls["TOOLBOX_IMAGE"] = toolboxes[arch]
            images.append((flavor, arch, param_urls, subvariant, imagetype))
    return images

def _find_duplicate_jobs(client, build, param_urls, flavor):
    """Check if we have any existing non-cancelled jobs for this
    build, ISO/HDD and flavor (checking flavor is important otherwise
    we'd bail on doing the per-ISO jobs for the ISO we use for the
    'universal' tests). ISO/HDD are taken from param_urls dict.
    """
    if any(par in param_urls for par in ('ISO_URL', 'HDD_1_DECOMPRESS_URL', 'HDD_1', 'HDD_2_DECOMPRESS_URL', 'HDD_2')):
        if 'ISO_URL' in param_urls:
            assetname = param_urls['ISO_URL'].split('/')[-1]
            jobs = client.openqa_request('GET', 'jobs', params={'iso': assetname, 'build': build})['jobs']
        elif 'HDD_1_DECOMPRESS_URL' in param_urls:
            # HDDs
            hddname = param_urls['HDD_1_DECOMPRESS_URL'].split('/')[-1]
            assetname = os.path.splitext(hddname)[0]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_1': assetname, 'build': build})['jobs']
        elif 'HDD_2_DECOMPRESS_URL' in param_urls:
            # HDDs
            hddname = param_urls['HDD_2_DECOMPRESS_URL'].split('/')[-1]
            assetname = os.path.splitext(hddname)[0]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_2': assetname, 'build': build})['jobs']
        elif 'HDD_1' in param_urls:
            assetname = param_urls['HDD_1'].split('/')[-1]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_1': assetname, 'build': build})['jobs']
        else:
            assetname = param_urls['HDD_2'].split('/')[-1]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_2': assetname, 'build': build})['jobs']

        jobs = [job for job in jobs if job['settings']['FLAVOR'] == flavor]
        jobs = [job for job in jobs if
                job.get('state') != 'cancelled' and job.get('result') != 'user_cancelled']
        if jobs:
            logger.info("run_openqa_jobs: Existing jobs found for asset %s flavor %s, and force "
                        "not set! No jobs scheduled.", assetname, flavor)
        return jobs
    return []


def _get_releases(release):
    """Get current, previous, rawhide and upgrade release params.
    Shared by compose and update paths. release is the release number
    or "Rawhide".
    """
    # find current and previous releases; these are used to determine
    # the hard disk image file names for the upgrade tests
    try:
        currrel = str(fedfind.helpers.get_current_release())
        rawrel = str(fedfind.helpers.get_current_release(branched=True) + 1)
    except ValueError:
        # we don't really want to bail entirely if fedfind failed for
        # some reason, let's just run the other tests and set a value
        # that shows what went wrong for the upgrade tests
        currrel = "FEDFINDERROR"
        # this *might* work...depends on bugs...
        rawrel = "rawhide"
    if str(release).isdigit():
        relnum = int(release)
    elif rawrel.isdigit():
        # assume it's Rawhide
        relnum = int(rawrel)
    else:
        # we're stuck
        relnum = None
    if relnum:
        # we want upgrade tests to test upgrade from one release
        # before the release under test, and upgrade_2 tests, upgrade
        # from two releases before
        up1rel = str(relnum - 1)
        up2rel = str(relnum - 2)
    else:
        up1rel = "FEDFINDERROR"
        up2rel = "FEDFINDERROR"

    return {
        "CURRREL": currrel,
        "UP1REL": up1rel,
        "UP2REL": up2rel,
        "RAWREL": rawrel,
    }


def run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, build, version,
                    location, force=False, extraparams=None, openqa_hostname=None, label=""):
    """# run OpenQA 'isos' job on ISO at urls from 'param_urls', with
    given URLs, flavor, arch, subvariant, imagetype, build identifier,
    and version. **NOTE**: 'build' is passed to openQA as BUILD and is
    later retrieved and parsed by report.py for wiki reporting; for
    this to work it should be a productmd/Pungi compose ID. Returns
    list of job IDs. If force is False, jobs will only be scheduled if
    there are no existing, non-cancelled jobs for the same ISO and
    flavor. If extraparams is specified, it must be a dict or
    something else that can be combined with a dict using `update`; it
    adds additional parameters (usually openQA variables) to the POST
    request. When extraparams is used, the BUILD value has '-EXTRA'
    appended to signify that this should not be considered a clean run
    for the build. openqa_hostname can be used to specify a particular
    host to schedule the jobs on, if not set, the client library will
    choose (see library documentation for details on how). You must
    have a key and secret in your openQA client library config for the
    chosen host.
    """
    logger.info("sending jobs to openQA")

    # starts OpenQA jobs
    params = {
        '_OBSOLETE': '1',
        '_ONLY_OBSOLETE_SAME_BUILD': '1',   # only obsolete pending jobs for same BUILD
        'DISTRI': 'fedora',
        'VERSION': version,
        'FLAVOR': flavor,
        'ARCH': arch,
        'BUILD': build,
        'LOCATION': location,
        'SUBVARIANT': subvariant,
        'IMAGETYPE': imagetype,
        'QEMU_HOST_IP': '172.16.2.2',
        'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24'
    }
    if label:
        params["LABEL"] = label
    params.update(_get_releases(release=version))

    if extraparams:
        params.update(extraparams)
        # mung the BUILD so this is not considered a 'real' test run
        params['BUILD'] = "{0}-EXTRA".format(params['BUILD'])

    params.update(param_urls)

    client = OpenQA_Client(openqa_hostname)

    if not force:
        duplicates = _find_duplicate_jobs(client, build, param_urls, flavor)
        if duplicates:
            logger.debug("Existing jobs found: %s", ' '.join(str(dupe['id']) for dupe in duplicates))
            return []

    output = client.openqa_request('POST', 'isos', params)
    logger.debug("run_openqa_jobs: executed")
    logger.debug("run_openqa_jobs: planned jobs: %s", output["ids"])

    return output["ids"]


def jobs_from_compose(location, wanted=None, force=False, extraparams=None, openqa_hostname=None, arches=None,
                      flavors=None):
    """Schedule jobs against a specific compose. Returns a 2-tuple
    of the compose ID and the list of job IDs.

    location is the top level of the compose. Note this value is
    provided by fedora-messaging 'pungi.compose.status.change'
    messages as 'location'.

    wanted is a dict defining which images from the compose we should
    schedule tests for. It is passed direct to _get_images(). The
    default set of tested images is specified in config.py. It can be
    overridden by a system-wide or per-user file as well as with this
    argument. The layout is, intentionally, a subset of the pungi
    images.json metadata file. Check config.py to see the layout and
    for more information.

    If force is False, for each ISO, jobs will only be scheduled if
    there are no existing, non-cancelled jobs for the same ISO and
    flavor.

    extraparams is passed through to `run_openqa_jobs()`. It can be
    a dict (or anything else that can be passed to `dict.update()`)
    containing arbitrary extra parameters to be included in the ISO
    post request (usually this will be to specify extra openQA vars).

    openqa_hostname is passed through as well. It specifies which
    openQA host to schedule the jobs on. If not set, the client lib
    will choose.

    arches is a list of arches to schedule jobs for; if specified,
    the image list will be filtered by the arches listed. If not
    passed here, we check the config file for a value (a comma-
    separated list) and use it if present, otherwise jobs will be
    scheduled for all arches in the image list.

    flavors is a list of flavors to schedule jobs for; if specified,
    the image list will be filtered to images whose flavor is in this
    list. For convenience, case is ignored.

    Of course arches and flavors are redundant with and less capable
    than WANTED, but are used to back a convenience feature in the
    CLI, letting you quickly schedule jobs for specific flavor(s)
    and/or arch(es) without having to edit a WANTED file.
    """
    if not wanted:
        wanted = WANTED
    if not arches:
        if CONFIG.get("schedule", "arches"):
            arches = CONFIG.get("schedule", "arches").split(",")
        else:
            arches = []
    try:
        rel = fedfind.release.get_release(url=location)
    except ValueError:
        raise TriggerException("Could not find a release at {0}".format(location))
    except UrlMatchError as err:
        # this is fedfind telling us it found a compose, but its URL
        # didn't match the URL we requested: this is bad
        raise TriggerException(str(err))
    except UnsupportedComposeError:
        # this is fine, we don't need to warn, just return empty
        # values
        logger.debug("Ignoring unsupported compose at %s", location)
        return ('', [])
    logger.debug("Finding images for compose %s in location %s", rel.cid, location)
    images = _get_images(rel, wanted=wanted)
    # these are 'special' upgrade flavors, not associated with any
    # image. We want to schedule them when testing 'full' composes
    # that have a generic tree, but not when testing 'partial'
    # composes that only produce images. fedfind's https_url_generic
    # is a good indicator of this. we also don't schedule for ELN
    if rel.https_url_generic and rel.release.lower() != "eln":
        images.extend(
            [
                ("Workstation-upgrade", "x86_64", {}, "Workstation", "upgrade"),
                ("Workstation-upgrade", "aarch64", {}, "Workstation", "upgrade"),
                # we set SUBVARIANT to 'Server' for the 'universal' tests for
                # historical reasons, that's what it usually wound as with the
                # old mechanism
                ("universal", "x86_64", {}, "Server", "upgrade"),
                ("universal", "aarch64", {}, "Server", "upgrade"),
                ("universal", "ppc64le", {}, "Server", "upgrade"),
            ]
        )
    if flavors:
        flavors = [flavor.lower() for flavor in flavors]
        logger.debug("Only scheduling jobs for flavors %s", ' '.join(flavors))
        images = [img for img in images if img[0].lower() in flavors]
    if arches:
        logger.debug("Only scheduling jobs for arches %s", ' '.join(arches))
        images = [img for img in images if img[1] in arches]

    if not images:
        raise TriggerException("Compose found, but no available images")
    # here we're checking if we only got the 'special' upgrade flavors
    # *and that's not what the user asked for*. if it's what the user
    # asked for we should still go ahead
    if all(img[0] in ("Workstation-upgrade", "universal") for img in images):
        if not flavors or not all(flav in ("workstation-upgrade", "universal") for flav in flavors):
            raise TriggerException("Compose found, but no available images")

    jobs = []

    # schedule per-image jobs
    release = rel.release
    for (flavor, arch, param_urls, subvariant, imagetype) in images:
        jobs.extend(run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, rel.cid,
                                    release, location, force=force, extraparams=extraparams,
                                    openqa_hostname=openqa_hostname, label=rel.label))

    # if we scheduled any jobs, and this is a Fedora candidate compose,
    # tag this build as 'important'
    # this prevents its jobs being obsoleted if a nightly compose shows
    # up while they're running, and prevents it being garbage-collected
    # don't do this for post-release nightlies that are *always*
    # candidates, though
    # using getattr as the 'respin' composes don't have these attrs
    if (
        jobs
        and getattr(rel, 'type', '') == 'production'
        and getattr(rel, 'product', '') == 'Fedora'
        and getattr(rel, 'release', '').lower() != 'eln'
    ):
        client = OpenQA_Client(openqa_hostname)
        # we expect group 1 to be 'fedora', this is the case on both
        # Fedora instances, but may not be on pet instances if you did
        # not create the groups in the 'normal' order
        params = {'text': "tag:{0}:important:candidate".format(rel.cid)}
        # just in case group 1 doesn't even exist...
        try:
            client.openqa_request('POST', 'groups/1/comments', params=params)
        except openqa_client.exceptions.RequestError:
            logger.warning("Adding comment to mark compose as 'candidate' failed! 'fedora' group is not 1?")

    return (rel.cid, jobs)


def jobs_from_fcosbuild(buildurl, flavors=None, force=False, extraparams=None, openqa_hostname=None):
    """Schedule jobs for the Fedora CoreOS build at the given URL
    (should be the top-level URL with meta.json in it).
    flavors can be an iterable of flavors to schedule, otherwise all
    known CoreOS flavors that are present in the build will be
    scheduled.
    If force is False, we will not create jobs if some already exist
    for the same version and flavor; if it's True, we will always
    create jobs.
    """
    flavdict = {
        "CoreOS-colive-iso": ("live-iso", "colive", "ISO_URL"),
    }
    url = f"{buildurl}/meta.json"
    metadata = fedfind.helpers.download_json(url)
    arch = metadata["coreos-assembler.basearch"]
    images = metadata["images"]
    version = metadata["buildid"]
    relnum = version.split(".")[0]
    build = f"Fedora-CoreOS-{version}"
    logger.info("Scheduling jobs for CoreOS release %s", version)
    jobs = []
    for (flavor, (form, imagetype, param)) in flavdict.items():
        if flavors and flavor not in flavors:
            # filtered out!
            continue
        path = images.get(form, {}).get("path")
        location = f"{buildurl}/{path}"
        if location:
            param_urls = {
                param: location,
            }
        else:
            # no image found, onto the next
            continue
        logger.debug("Arch: %s", arch)
        logger.debug("Flavor: %s", flavor)
        logger.debug("Format: %s", form)
        logger.debug("Image type: %s", imagetype)
        logger.debug("Location: %s", location)
        jobs.extend(run_openqa_jobs(param_urls, flavor, arch, "CoreOS", imagetype, build,
                                    relnum, "", force=force, extraparams=extraparams,
                                    openqa_hostname=openqa_hostname))
    return jobs


def get_critpath_flavors(updic):
    """Given the dict for an update, determine the critical path
    flavors.
    """
    flavors = set()
    cpgroups = updic.get("critpath_groups")
    if cpgroups:
        cpgroups = cpgroups.split(" ")
        for cpgroup in cpgroups:
            flavors.update(UPDATE_FLAVORS.get(cpgroup, tuple()))
    return flavors


def get_testlist_flavors(updic):
    """Given the dict for an update, determine any flavors from
    the UPDATETL config list.
    """
    flavors = set()
    for build in updic.get('builds', []):
        # get just the package name by splitting the NVR. This
        # assumes all NVRs actually contain a V and an R.
        # Happily, RPM rejects dashes in version or release.
        pkgname = build['nvr'].rsplit('-', 2)[0]
        # now check the list and adjust flavors
        if pkgname in UPDATETL:
            flavors.update(UPDATETL[pkgname])
    return flavors


def jobs_from_update(
        update,
        version=None,
        flavors=None,
        force=False,
        extraparams=None,
        openqa_hostname=None,
        arch=None,
        updic=None
    ):
    """Schedule jobs for a specific Fedora update (or scratch build).

    update (str): advisory ID, task ID, or side tag name
    version (str or None): the release number; for updates will be
    discovered from Bodhi if not given, for tasks it must be given
    flavors (iter of strs or None): defines which update tests should
    be run (valid values are the 'flavdict' keys). If None, will
    schedule all flavors
    force (bool): see jobs_from_compose
    extraparams (dict): see jobs_from_compose
    openqa_hostname (str or None): see jobs_from_compose
    arch (str): arch to schedule for
    updic (dict or None): the Bodhi update dict, from the message or
    the web API. Must be provided to schedule update jobs
    """
    if version:
        version = str(version)
    if not flavors:
        flavors = set()
        for flavlist in UPDATE_FLAVORS.values():
            flavors.update(flavlist)
    if not arch:
        # set a default in a way that works neatly with the CLI bits
        arch = 'x86_64'
    if isinstance(update, str) and update.isdigit():
        update = [update]
    if isinstance(update, list):
        if not all(item.isdigit() for item in update):
            raise TriggerException("Can only pass multiple Koji tasks, not updates or side tags!")
        idstring = "_".join(update)
        # Koji task ID: treat as a non-reported scratch build test
        build = f"Kojitask-{idstring}-NOREPORT"
        # we'll set ADVISORY and ADVISORY_OR_TASK for updates, and KOJITASK and
        # ADVISORY_OR_TASK for Koji tasks. I'd probably have designed this more
        # cleanly if doing it from scratch, but we started with updates and added
        # tasks later and it's a bit messy. We need to have a consistently-named
        # variable for the distri templates substitution, there's no mechanism to
        # do 'substitute for this var or this other var depending which exists'
        advkey = 'KOJITASK'
        advval = idstring
        updrepo = "nfs://172.16.2.110:/mnt/update_repo"
        baseparams = {}
        if not version:
            raise TriggerException("Must provide version when scheduling a Koji task!")
    elif update.startswith("TAG_"):
        # we're testing a side tag
        build = f"{update}-NOREPORT"
        update = update[4:]
        advkey = 'TAG'
        advval = update
        baseparams = {}
        updrepo = f"https://kojipkgs.fedoraproject.org/repos/{update}/latest/{arch}"
        if not version:
            raise TriggerException("Must provide version when scheduling a Koji tag!")
    else:
        # normal update case
        build = 'Update-{0}'.format(update)
        advkey = 'ADVISORY'
        advval = update
        updrepo = "nfs://172.16.2.110:/mnt/update_repo"
        # now we retrieve the list of NVRs in the update as of right now and
        # include them as variables; the test will download and test those
        # NVRs. We do this instead of the test just using bodhi CLI to get
        # whatever's in the update at the time the test runs so we can publish
        # correct CI Messages:
        # https://pagure.io/fedora-qa/fedora_openqa/issue/78
        if not updic:
            raise ValueError("Update dict must be provided to schedule update jobs!")
        builds = updic['builds']
        nvrs = [build['nvr'] for build in builds]
        if not version:
            # find version in update data
            version = updic['release']['version']
        baseparams = {}
        # chunk the nvr list, to avoid awkward problems with very
        # long values like https://progress.opensuse.org/issues/121054
        chunksize = 20
        chunked_nvrs = [nvrs[i:i+chunksize] for i in range(0, len(nvrs), chunksize)]
        for (num, cnvrs) in enumerate(chunked_nvrs, 1):
            # we split the list across multiple settings because a
            # surprising amount of tricky bugs show up if a settings
            # value is very long, e.g.:
            # https://progress.opensuse.org/issues/121054
            baseparams[f'ADVISORY_NVRS_{num}'] = ' '.join(cnvrs)

    if extraparams:
        build = '{0}-EXTRA'.format(build)
    baseparams.update({
        'DISTRI': 'fedora',
        'VERSION': version,
        'ARCH': arch,
        'BUILD': build,
        advkey: advval,
        'ADVISORY_OR_TASK': advval,
        'UPDATE_OR_TAG_REPO': updrepo,
        # only obsolete pending jobs for same BUILD (i.e. update)
        '_OBSOLETE': '1',
        '_ONLY_OBSOLETE_SAME_BUILD': '1',
        # many update tests are shared with compose and specify
        # START_AFTER_TEST as '%DEPLOY_UPLOAD_TEST%', so for compose
        # they run after an initial install. For updates we mainly
        # want to run these tests using a base image, hence this empty
        # value for START_AFTER_TEST. For a few update tests which do
        # have a deployment step, we specify +START_AFTER_TEST in the
        # templates; the + makes that value win over this one.
        'START_AFTER_TEST': '',
        'QEMU_HOST_IP': '172.16.2.2',
        'NICTYPE_USER_OPTIONS': 'net=172.16.2.0/24',
    })

    # get the release params
    relparams = _get_releases(release=version)
    if relparams["CURRREL"] == "FEDFINDERROR":
        # we do something a bit different for updates if fedfind failed
        logger.warning("jobs_from_update: could not determine current release! Assuming current "
                       "release is same as update release. This may cause some tests to fail "
                       "if that is not true.")
        relparams["CURRREL"] = version

    # find oldest release
    try:
        stables = fedfind.helpers.get_current_stables()
        oldest = min(stables)
    except ValueError:
        # but don't fail to schedule if fedfind fails...
        logger.warning("jobs_from_update: could not determine oldest release! Assuming update/task is "
                       "for stable release that is not the oldest stable.")
        oldest = 0
    client = OpenQA_Client(openqa_hostname)
    jobs = []

    for flavor in flavors:
        if int(version) == oldest and 'upgrade' in flavor:
            # we don't want to run upgrade tests in this case; we
            # don't support upgrade from EOL releases, and we don't
            # keep the necessary base disk images around
            logger.debug("skipping upgrade tests as release %s is the oldest stable", version)
            continue
        fullflav = 'updates-{0}'.format(flavor)
        if not force:
            # dupe check
            currjobs = client.openqa_request('GET', 'jobs', params={'build': build, 'arch': arch})['jobs']
            currjobs = [cjob for cjob in currjobs if cjob['settings']['FLAVOR'] == fullflav]
            if currjobs:
                logger.info("jobs_from_update: Existing jobs found for update/task %s flavor %s arch %s, "
                            "and force not set! No jobs scheduled.", advval, flavor, arch)
                continue
        # we start from the relparams, as we want later-read param
        # dicts to override them sometimes
        fullparams = relparams.copy()
        # add in the base params
        fullparams.update(baseparams)
        fullparams['FLAVOR'] = fullflav
        if extraparams:
            fullparams.update(extraparams)
        output = client.openqa_request('POST', 'isos', data=fullparams)
        logger.debug("jobs_from_update: planned %s jobs: %s", flavor, output["ids"])
        jobs.extend(output["ids"])

    return jobs

# vim: set textwidth=120 ts=8 et sw=4:
