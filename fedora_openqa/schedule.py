# Copyright (C) 2015 Red Hat Inc.
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
import fedfind.helpers
import fedfind.release
from openqa_client.client import OpenQA_Client

# Internal dependencies
from .config import WANTED

logger = logging.getLogger(__name__)

FORMAT_TO_PARAM = {
    "iso": "ISO_URL",
    # let's connect it as second HDD - we can then use NUMDISKS=1 when we don't need it connected
    "raw.xz": "HDD_2_DECOMPRESS_URL"
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
            # FIXME: this is technically too simple though it works
            # for all releases we currently test; see fedfind 'alt'
            # location handling
            url = "{0}/{1}".format(rel.location, foundimg['path'])
            # fedfind gives us 'download.fedoraproject.org' for respins, but
            # we don't want to go through the roulette...
            url = url.replace('download.fedoraproject.org', 'dl.fedoraproject.org')
            logger.debug("Found image %s for arch %s at %s", flavor, arch, url)

            # some tests need more than one file, so let's collect them now
            param_urls = {
                FORMAT_TO_PARAM[foundimg['format']]: url
            }
            # if direct kernel boot is specified, we need to download kernel and initrd
            if wantimg.get('dkboot', False):
                (kernel_url, initrd_url) = _get_dkboot_urls(rel.https_url_generic, arch)
                param_urls["KERNEL_URL"] = kernel_url
                param_urls["KERNEL"] = "{0}.{1}.vmlinuz".format(rel.cid, arch)
                param_urls["INITRD_URL"] = initrd_url
                param_urls["INITRD"] = "{0}.{1}.initrd.img".format(rel.cid, arch)

            images.append((flavor, arch, score, param_urls, subvariant, imagetype))
    return images


def _find_duplicate_jobs(client, param_urls, flavor):
    """Check if we have any existing non-cancelled jobs for this
    ISO/HDD and flavor (checking flavor is important otherwise we'd
    bail on doing the per-ISO jobs for the ISO we use for the
    'universal' tests). ISO/HDD are taken from param_urls dict.
    """
    if any([param in param_urls for param in ('ISO_URL', 'HDD_1_DECOMPRESS_URL', 'HDD_1')]):
        if 'ISO_URL' in param_urls:
            assetname = param_urls['ISO_URL'].split('/')[-1]
            jobs = client.openqa_request('GET', 'jobs', params={'iso': assetname})['jobs']
        elif 'HDD_1_DECOMPRESS_URL' in param_urls:
            # HDDs
            hddname = param_urls['HDD_1_DECOMPRESS_URL'].split('/')[-1]
            assetname = os.path.splitext(hddname)[0]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_1': assetname})['jobs']
        else:
            assetname = param_urls['HDD_1'].split('/')[-1]
            jobs = client.openqa_request('GET', 'jobs', params={'hdd_1': assetname})['jobs']

        jobs = [job for job in jobs if job['settings']['FLAVOR'] == flavor]
        jobs = [job for job in jobs if
                job.get('state') != 'cancelled' and job.get('result') != 'user_cancelled']
        if jobs:
            logger.info("run_openqa_jobs: Existing jobs found for asset %s flavor %s, and force "
                        "not set! No jobs scheduled.", assetname, flavor)
        return jobs
    return []


def run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, build, version,
                    location, force=False, extraparams=None, openqa_hostname=None):
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
    # find current and previous releases; these are used to determine
    # the hard disk image file names for the upgrade tests
    try:
        currrel = str(fedfind.helpers.get_current_release())
        prevrel = str(int(currrel) - 1)
    except ValueError:
        # we don't really want to bail entirely if fedfind failed for
        # some reason, let's just run the other tests and set a value
        # that shows what went wrong for the upgrade tests
        currrel = prevrel = "FEDFINDERROR"

    # starts OpenQA jobs
    params = {
        'DISTRI': 'fedora',
        'VERSION': version,
        'FLAVOR': flavor,
        'ARCH': arch if arch != 'armhfp' else 'arm',  # openQA does something special when `ARCH = arm`
        'BUILD': build,
        'LOCATION': location,
        'CURRREL': currrel,
        'PREVREL': prevrel,
        'SUBVARIANT': subvariant,
        'IMAGETYPE': imagetype,
        # FIXME: this is a workaround for
        # https://bugzilla.redhat.com/show_bug.cgi?id=1430043 , should
        # be removed when that is fixed
        'CDMODEL': 'ide-cd',
    }
    if extraparams:
        params.update(extraparams)
        # mung the BUILD so this is not considered a 'real' test run
        params['BUILD'] = "{0}-EXTRA".format(params['BUILD'])

    params.update(param_urls)

    client = OpenQA_Client(openqa_hostname)

    if not force:
        duplicates = _find_duplicate_jobs(client, param_urls, flavor)
        if duplicates:
            logger.debug("Existing jobs found: %s", ' '.join(str(dupe['id']) for dupe in duplicates))
            return []

    output = client.openqa_request('POST', 'isos', params)
    logger.debug("run_openqa_jobs: executed")
    logger.debug("run_openqa_jobs: planned jobs: %s", output["ids"])

    return output["ids"]


def jobs_from_compose(location, wanted=None, force=False, extraparams=None, openqa_hostname=None):
    """Schedule jobs against a specific compose. Returns a 2-tuple
    of the compose ID and the list of job IDs.

    location is the top level of the compose. Note this value is
    provided by fedmsg 'pungi.compose.status.change' messages as
    'location'.

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
    """
    if not wanted:
        wanted = WANTED
    try:
        rel = fedfind.release.get_release(url=location)
    except ValueError:
        raise TriggerException("Could not find a release at {0}".format(location))
    logger.debug("Finding images for compose %s in location %s", rel.cid, location)
    images = _get_images(rel, wanted=wanted)
    if len(images) == 0:
        raise TriggerException("Compose found, but no available images")
    jobs = []
    univs = {}

    # schedule per-image jobs, keeping track of the highest score
    # per arch along the way
    for (flavor, arch, score, param_urls, subvariant, imagetype) in images:
        jobs.extend(run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, rel.cid,
                                    rel.release, location, force=force, extraparams=extraparams,
                                    openqa_hostname=openqa_hostname))
        if score > univs.get(arch, [None, 0])[1]:
            univs[arch] = (param_urls, score, subvariant, imagetype)

    # now schedule universal jobs
    if univs:
        for (arch, (param_urls, _, subvariant, imagetype)) in univs.items():
            # We are assuming that ISO_URL is present in param_urls. This could create problem when
            # unversal tests are run on product that doesn't have ISO. OTOH, only product without ISO
            # is ARM and there would be whole lot of other problems if universal tests are run on ARM.
            logger.info("running universal tests for %s with %s", arch, param_urls['ISO_URL'])
            jobs.extend(run_openqa_jobs(param_urls, 'universal', arch, subvariant, imagetype,
                                        rel.cid, rel.release, location, force=force,
                                        extraparams=extraparams, openqa_hostname=openqa_hostname))

    # if we scheduled any jobs, and this is a candidate compose, tag
    # this build as 'important'
    # this prevents its jobs being obsoleted if a nightly compose shows
    # up while they're running, and prevents it being garbage-collected
    # don't do this for post-release nightlies that are *always*
    # candidates, though
    if rel.type == 'production' and rel.product == 'Fedora' and jobs:
        client = OpenQA_Client(openqa_hostname)
        # we expect group 1 to be 'fedora'. I think this is reliable.
        params = {'text': "tag:{0}:important:candidate".format(rel.cid)}
        client.openqa_request('POST', 'groups/1/comments', params=params)

    return (rel.cid, jobs)

def jobs_from_update(update, version, flavors=None, force=False, extraparams=None, openqa_hostname=None):
    """Schedule jobs for a specific Fedora update. update is the
    advisory ID, version is the release number, flavors defines which
    update tests should be run (valid values are the 'flavdict' keys).
    force, extraparams and openqa_hostname are as for
    jobs_from_compose. To explain the HDD_1 and START_AFTER_TEST
    settings: most tests in the 'update' scenario are shared with the
    'compose' scenario. Many of them specify START_AFTER_TEST as
    'install_default_upload' and HDD_1 as the disk image that
    install_default_upload creates, so that in the 'compose' scenario,
    these tests run after install_default_upload and use the image it
    creates. For update testing, there is no install_default_upload
    test; we instead want to run these tests using the pre-existing
    createhdds-created base image. So here, we specify the appropriate
    HDD_1 value, and an empty value for START_AFTER_TEST, so the
    scheduler will not try to create a dependency on the non-existent
    install_default_upload test, and the correct disk image will be
    used. There are a *few* tests where we do *not* want to override
    these values, however: the tests where there really is a dependency
    in both scenarios (e.g. the cockpit_basic test has to run after the
    cockpit_default test and use the disk image it uploads). For these
    tests, we specify the values in the templates as +START_AFTER_TEST
    and +HDD_1; the + makes those values win over the ones we pass in
    here.
    """
    version = str(version)
    build = 'Update-{0}'.format(update)
    if extraparams:
        build = '{0}-EXTRA'.format(build)
    flavdict = {
        'server': {
            'HDD_1': 'disk_f{0}_server_3_x86_64.img'.format(version),
        },
        'workstation': {
            'HDD_1': 'disk_f{0}_desktop_3_x86_64.img'.format(version),
            'DESKTOP': 'gnome',
        },
    }
    baseparams = {
        'DISTRI': 'fedora',
        'VERSION': version,
        'ARCH': 'x86_64',
        'BUILD': build,
        'ADVISORY': update,
        # this disables the openQA logic that cancels all running jobs
        # with the same DISTRI, VERSION, FLAVOR and ARCH
        '_NOOBSOLETEBUILD': 1,
        # FIXME: this is a workaround for
        # https://bugzilla.redhat.com/show_bug.cgi?id=1430043 , should
        # be removed when that is fixed
        'CDMODEL': 'ide-cd',
        'START_AFTER_TEST': '',
    }
    # mark if release is a development release; the tests need to know
    try:
        curr = int(fedfind.helpers.get_current_release())
        if str(version).lower() == 'rawhide' or int(version) > curr:
            baseparams['DEVELOPMENT'] = 1
    except ValueError:
        # but don't fail to schedule if fedfind fails...
        logger.warning("jobs_from_update: could not determine current release! Assuming update is "
                       "for stable release.")
    client = OpenQA_Client(openqa_hostname)
    jobs = []

    if not flavors:
        flavors = flavdict.keys()

    for flavor in flavors:
        fullflav = 'updates-{0}'.format(flavor)
        if not force:
            # dupe check
            currjobs = client.openqa_request('GET', 'jobs', params={'build': build})['jobs']
            currjobs = [cjob for cjob in currjobs if cjob['settings']['FLAVOR'] == fullflav]
            if currjobs:
                logger.info("jobs_from_update: Existing jobs found for update %s flavor %s, and force "
                            "not set! No jobs scheduled.", update, flavor)
                continue
        flavparams = flavdict[flavor]
        flavparams.update(baseparams)
        flavparams['FLAVOR'] = fullflav
        if extraparams:
            flavparams.update(extraparams)
        output = client.openqa_request('POST', 'isos', flavparams)
        logger.debug("jobs_from_update: planned %s jobs: %s", flavor, output["ids"])
        jobs.extend(output["ids"])

    return jobs

# vim: set textwidth=120 ts=8 et sw=4:
