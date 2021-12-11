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

# Internal dependencies
from .config import WANTED, CONFIG

logger = logging.getLogger(__name__)

FORMAT_TO_PARAM = {
    "iso": "ISO_URL",
    # let's connect it as second HDD - we can then use NUMDISKS=1 when we don't need it connected
    "raw.xz": "HDD_2_DECOMPRESS_URL",
    "qcow2": "HDD_2_URL",
}


class TriggerException(Exception):
    pass


def _get_dkboot_urls(location, arch='armhfp'):
    """Given a fedfind release 'generic' location (and arch if provided), return URLs for kernel
    and initrd files.
    """
    pxeboot_url = '{0}/{1}/os/images/pxeboot/{2}'
    return (pxeboot_url.format(location, arch, 'vmlinuz'), pxeboot_url.format(location, arch, 'initrd.img'))


def _get_images(rel, wanted=None):
    """Given a fedfind Release instance, this returns a list of (flavor, arch, score, {param: url},
    subvariant, imagetype) tuples for images to be tested.
    """
    if not wanted:
        wanted = WANTED
    images = []
    for wantimg in wanted:
        matchdict = wantimg['match'].copy()
        for foundimg in rel.all_images:
            # see if the foundimg matches the wantimg
            if not all(item in foundimg.items() for item in matchdict.items()):
                continue
            score = wantimg.get('score', 0)
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
            if 'updates-testing' in rel.cid:
                # image names in 'updates-testing' and 'updates' composes
                # are the same. we need to set a custom filename for the
                # image for updates-testing composes to avoid a clash
                fileparam = FORMAT_TO_PARAM[foundimg['format']].split('_URL')[0]
                filename = os.path.basename(foundimg['path'])
                param_urls[fileparam] = 'testing-' + filename
            # if direct kernel boot is specified, we need to download kernel and initrd
            if wantimg.get('dkboot', False):
                (kernel_url, initrd_url) = _get_dkboot_urls(rel.https_url_generic, arch)
                param_urls["KERNEL_URL"] = kernel_url
                param_urls["KERNEL"] = "{0}.{1}.vmlinuz".format(rel.cid, arch)
                param_urls["INITRD_URL"] = initrd_url
                param_urls["INITRD"] = "{0}.{1}.initrd.img".format(rel.cid, arch)

            images.append((flavor, arch, score, param_urls, subvariant, imagetype))
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
        prevrel = str(int(currrel) - 1)
        rawrel = str(fedfind.helpers.get_current_release(branched=True) + 1)
    except ValueError:
        # we don't really want to bail entirely if fedfind failed for
        # some reason, let's just run the other tests and set a value
        # that shows what went wrong for the upgrade tests
        currrel = prevrel = "FEDFINDERROR"
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
        "PREVREL": prevrel,
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
        'ARCH': arch if arch != 'armhfp' else 'arm',  # openQA does something special when `ARCH = arm`
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

    # for now, only images from composes with Modular in the name are
    # modular; we may need to change this in future as modular goes
    # mainstream
    if 'Modular' in build:
        params['MODULAR'] = '1'

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
    images.json metadata file (except for the 'score' item). Check
    config.py to see the layout and for more information.

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
    # is a good indicator of this.
    if rel.https_url_generic:
        images.extend(
            [
                ("Workstation-upgrade", "x86_64", 0, {}, "Workstation", "upgrade"),
                ("Workstation-upgrade", "aarch64", 0, {}, "Workstation", "upgrade"),
            ]
        )
    if flavors and flavors != ["universal"]:
        # in special cast flavors is just "universal", we don't filter
        # the image list so we can pick the best universal candidate
        flavors = [flavor.lower() for flavor in flavors]
        logger.debug("Only scheduling jobs for flavors %s", ' '.join(flavors))
        images = [img for img in images if img[0].lower() in flavors]
    if arches:
        logger.debug("Only scheduling jobs for arches %s", ' '.join(arches))
        images = [img for img in images if img[1] in arches]

    if not images or (all(img[0] == "Workstation-upgrade" for img in images) and flavors != ["Workstation-upgrade"]):
        raise TriggerException("Compose found, but no available images")
    jobs = []
    univs = {}

    # schedule per-image jobs, keeping track of the highest score
    # per arch along the way
    release = rel.release
    # for sanity's sake let's just treat the stupid-ass 'Bikeshed'
    # version as 'Rawhide' for now
    if release.lower() == 'bikeshed':
        release = 'Rawhide'
    for (flavor, arch, score, param_urls, subvariant, imagetype) in images:
        if flavors != ["universal"]:
            # in the special case that flavors is just "universal", we
            # don't want to schedule jobs, only work out univ cands
            jobs.extend(run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, rel.cid,
                                        release, location, force=force, extraparams=extraparams,
                                        openqa_hostname=openqa_hostname, label=rel.label))
        if score > univs.get(arch, [None, 0])[1]:
            univs[arch] = (param_urls, score, subvariant, imagetype)

    # now schedule universal jobs...unless 'flavors' was passed and
    # 'universal' wasn't in it
    if flavors and 'universal' not in flavors:
        univs = {}
    if univs:
        for (arch, (param_urls, _, subvariant, imagetype)) in univs.items():
            # We are assuming that ISO_URL is present in param_urls. This could create problem when
            # unversal tests are run on product that doesn't have ISO. OTOH, only product without ISO
            # is ARM and there would be whole lot of other problems if universal tests are run on ARM.
            logger.info("running universal tests for %s with %s", arch, param_urls['ISO_URL'])
            jobs.extend(run_openqa_jobs(param_urls, 'universal', arch, subvariant, imagetype,
                                        rel.cid, release, location, force=force,
                                        extraparams=extraparams, openqa_hostname=openqa_hostname,
                                        label=rel.label))

    # if we scheduled any jobs, and this is a candidate compose, tag
    # this build as 'important'
    # this prevents its jobs being obsoleted if a nightly compose shows
    # up while they're running, and prevents it being garbage-collected
    # don't do this for post-release nightlies that are *always*
    # candidates, though
    # using getattr as the 'respin' composes don't have these attrs
    if getattr(rel, 'type', '') == 'production' and getattr(rel, 'product', '') == 'Fedora':
        # we don't want to tag all updates / updates-testing composes
        if 'updates' not in getattr(rel, 'milestone', '').lower() and jobs:
            client = OpenQA_Client(openqa_hostname)
            # we expect group 1 to be 'fedora'. I think this is reliable.
            params = {'text': "tag:{0}:important:candidate".format(rel.cid)}
            client.openqa_request('POST', 'groups/1/comments', params=params)

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


def jobs_from_update(update, version, flavors=None, force=False, extraparams=None, openqa_hostname=None, arch=None):
    """Schedule jobs for a specific Fedora update (or scratch build).
    update is the advisory ID or task ID, version is the release
    number, flavors defines which update tests should be run (valid
    values are the 'flavdict' keys). force, extraparams and
    openqa_hostname are as for jobs_from_compose. To explain the HDD_1
    and START_AFTER_TEST settings: most tests in the 'update' scenario
    are shared with the 'compose' scenario. Many of them specify
    START_AFTER_TEST as 'install_default_upload' and HDD_1 as the disk
    image that install_default_upload creates, so that in the compose
    scenario, these tests run after install_default_upload and use the
    image it creates. For update testing, there is no install_default_
    upload test; we instead want to run these tests using the pre-
    existing createhdds-created base image. So here, we specify the
    appropriate HDD_1 value, and an empty value for START_AFTER_TEST,
    so the scheduler will not try to create a dependency on the non-
    existent install_default_upload test, and the correct disk image
    will be used. There are a *few* tests where we do *not* want to
    override these values, however: the tests where there really is a
    dependency in both scenarios (e.g. the cockpit_basic test has to
    run after the cockpit_default test and use the disk image it
    uploads). For these tests, we specify the values in the templates
    as +START_AFTER_TEST and +HDD_1; the + makes those values win over
    the ones we pass in here.
    """
    version = str(version)
    # Bail if version looks like Rawhide version, because we do
    # not really want to run tests on Rawhide updates yet. There
    # is no mechanism for combining interdependent packages into
    # one update, so we will get failures, and generating base
    # disk images for Rawhide is pretty unreliable.
    try:
        if int(version) > fedfind.helpers.get_current_release(branched=True):
            logger.info("jobs_from_update: Not scheduling jobs for update %s as it appears to be for "
                        "Rawhide!", update)
            return []
    except ValueError:
        # but don't fail to schedule if fedfind fails...
        logger.warning("jobs_from_update: could not check if update %s is for Rawhide! Scheduling "
                       "anyway. Tests will fail if this update is for Rawhide.", update)

    if not arch:
        # set a default in a way that works neatly with the CLI bits
        arch = 'x86_64'
    if update.isdigit():
        # Koji task ID: treat as a non-reported scratch build test
        build = "Kojitask-{0}-NOREPORT".format(update)
    else:
        # normal update case
        build = 'Update-{0}'.format(update)
    if extraparams:
        build = '{0}-EXTRA'.format(build)
    flavdict = {
        'container': {
            # this flavor uses the server base image
            'HDD_1': 'disk_f{0}_server_3_{1}.qcow2'.format(version, arch),
        },
        'server': {
            'HDD_1': 'disk_f{0}_server_3_{1}.qcow2'.format(version, arch),
        },
        'server-upgrade': {},
        'kde': {
            'HDD_1': 'disk_f{0}_kde_4_{1}.qcow2'.format(version, arch),
            'DESKTOP': 'kde',
        },
        'kde-live-iso': {
            'SUBVARIANT': 'KDE',
        },
        'workstation': {
            'HDD_1': 'disk_f{0}_desktop_4_{1}.qcow2'.format(version, arch),
            'DESKTOP': 'gnome',
        },
        'workstation-upgrade': {},
        'workstation-live-iso': {
            'SUBVARIANT': 'Workstation',
        },
        'everything-boot-iso': {},
    }
    # we'll set ADVISORY and ADVISORY_OR_TASK for updates, and KOJITASK and
    # ADVISORY_OR_TASK for Koji tasks. I'd probably have designed this more
    # cleanly if doing it from scratch, but we started with updates and added
    # tasks later and it's a bit messy. We need to have a consistently-named
    # variable for the distri templates substitution, there's no mechanism to
    # do 'substitute for this var or this other var depending which exists'
    if update.isdigit():
        advkey = 'KOJITASK'
        baseparams = {}
    else:
        advkey = 'ADVISORY'
        # now we retrieve the list of NVRs in the update as of right now and
        # include it as a variable; the test will download and test those
        # NVRs. We do this instead of the test just using bodhi CLI to get
        # whatever's in the update at the time the test runs so we can publish
        # correct CI Messages:
        # https://pagure.io/fedora-qa/fedora_openqa/issue/78
        url = 'https://bodhi.fedoraproject.org/updates/' + update
        builds = fedfind.helpers.download_json(url)['update']['builds']
        nvrs = [build['nvr'] for build in builds]
        baseparams = {'ADVISORY_NVRS': ' '.join(nvrs)}
    baseparams.update({
        'DISTRI': 'fedora',
        'VERSION': version,
        'ARCH': arch,
        'BUILD': build,
        advkey: update,
        'ADVISORY_OR_TASK': update,
        # only obsolete pending jobs for same BUILD (i.e. update)
        '_OBSOLETE': '1',
        '_ONLY_OBSOLETE_SAME_BUILD': '1',
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
        relparams["CURRREL"] = str(version)
        relparams["PREVREL"] = str(int(version) - 1)

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

    if not flavors:
        flavors = flavdict.keys()

    for flavor in flavors:
        if int(version) == oldest and 'upgrade' in flavor:
            # we don't want to run upgrade tests in this case; we
            # don't support upgrade from EOL releases, and we don't
            # keep the necessary base disk images around
            logger.debug("skipping upgrade tests as release %s is the oldest stable", version)
            continue
        if int(version) == 32 and flavor == "kde-live-iso":
            # KDE live image build for F32 just hangs in the middle of
            # nss, and F32 will be EOL soon, so let's just skip it
            logger.debug("skipping kde-live-iso for F32 due to known bug")
            continue
        fullflav = 'updates-{0}'.format(flavor)
        if not force:
            # dupe check
            currjobs = client.openqa_request('GET', 'jobs', params={'build': build, 'arch': arch})['jobs']
            currjobs = [cjob for cjob in currjobs if cjob['settings']['FLAVOR'] == fullflav]
            if currjobs:
                logger.info("jobs_from_update: Existing jobs found for update/task %s flavor %s arch %s, "
                            "and force not set! No jobs scheduled.", update, flavor, arch)
                continue
        # we start from the relparams, as we want later-read param
        # dicts to override them sometimes
        fullparams = relparams.copy()
        # add in the per-flavor params
        fullparams.update(flavdict[flavor])
        # add in the base params
        fullparams.update(baseparams)
        fullparams['FLAVOR'] = fullflav
        if extraparams:
            fullparams.update(extraparams)
        output = client.openqa_request('POST', 'isos', fullparams)
        logger.debug("jobs_from_update: planned %s jobs: %s", flavor, output["ids"])
        jobs.extend(output["ids"])

    return jobs

# vim: set textwidth=120 ts=8 et sw=4:
