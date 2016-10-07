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

"""Scheduler module for fedora-openqa-schedule. Functions related to
job scheduling go here.
"""

# Standard libraries
import json
import logging
import os.path
import re

# External dependencies
import fedfind.helpers
from openqa_client.client import OpenQA_Client
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import URLError, HTTPError
from resultsdb_api import ResultsDBapi, ResultsDBapiException

# Internal dependencies
from fedora_openqa_schedule.config import CONFIG, WANTED

logger = logging.getLogger(__name__)

FORMAT_TO_PARAM = {
    "iso": "ISO_URL",
    # let's connect it as second HDD - we can then use NUMDISKS=1 when we don't need it connected
    "raw.xz": "HDD_2_DECOMPRESS_URL"
}


class TriggerException(Exception):
    pass


def _get_compose_id(location):
    """Given a compose location, find the compose ID. Really we'd like
    taskotron to give us this, as fedmsg provides it, but taskotron is
    kinda tied to giving us just *one* variable property of the fedmsg
    message. So we read it from the compose metadata's known location.
    """
    try:
        resp = urlopen('{0}/metadata/composeinfo.json'.format(location))
        metadata = json.load(resp)
    except (ValueError, URLError, HTTPError):
        raise TriggerException("Compose not found, or failed!")
    return metadata['payload']['compose']['id']


def _get_dkboot_urls(location, arch='armhfp'):
    """Given a compose location (and arch if provided), return URLs for kernel and initrd
    files.
    """
    pxeboot_url = '{0}/Everything/{1}/os/images/pxeboot/{2}'
    return pxeboot_url.format(location, arch, 'vmlinuz'), pxeboot_url.format(location, arch, 'initrd.img')


def _get_images(location, wanted=WANTED):
    """Given a Pungi compose top-level location, this returns a list
    of (flavor, arch, score, {param: url}, subvariant, imagetype) tuples for images to be tested.
    """
    try:
        resp = urlopen('{0}/metadata/images.json'.format(location))
        metadata = json.load(resp)
    except (ValueError, URLError, HTTPError):
        raise TriggerException("Compose not found, or failed!")
    images = []
    for variant in wanted.keys():
        for arch in wanted[variant].keys():
            try:
                foundimgs = metadata['payload']['images'][variant][arch]
            except KeyError:
                # not found in upstream metadata, move on
                continue

            wantimgs = wanted[variant][arch]
            for wantimg in wantimgs:
                matchdict = wantimg['match'].copy()
                for foundimg in foundimgs:
                    # let fedfind 'correct' the foundimg dict (fixes
                    # problems with upstream metadata values)
                    foundimg = fedfind.helpers.correct_image(foundimg)
                    # see if the foundimg matches the wantimg
                    if not all(item in foundimg.items() for item in matchdict.items()):
                        continue
                    score = wantimg.get('score', 0)
                    # assign a 'flavor' using fedfind's 'image identifier'
                    flavor = fedfind.helpers.identify_image(foundimg, undersub=True, out='string')
                    # get a couple of values we use for other reasons
                    subvariant = foundimg['subvariant']
                    imagetype = foundimg['type']
                    url = "{0}/{1}".format(location, foundimg['path'])
                    logger.debug("Found image %s for arch %s at %s", flavor, arch, url)

                    # some tests need more than one file, so let's collect them now
                    param_urls = {
                        FORMAT_TO_PARAM[foundimg['format']]: url
                    }
                    # TODO: WARNING! - workaround for ARM disk images that need kernel for direct kernel boot
                    if arch == "armhfp" and foundimg['format'] == "raw.xz":
                        kernel_url, initrd_url = _get_dkboot_urls(location, arch)
                        param_urls["KERNEL_URL"] = kernel_url
                        param_urls["INITRD_URL"] = initrd_url

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


def run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, build,
                    location, force=False, extraparams=None, resultsdb_job_id=None):
    """# run OpenQA 'isos' job on ISO at urls from 'param_urls', with given arch
    and a build identifier. **NOTE**: 'build' is passed to openQA as
    BUILD and is later retrieved and parsed by report.py for wiki
    report generation. Returns list of job IDs. If force is False,
    jobs will only be scheduled if there are no existing,
    non-cancelled jobs for the same ISO and flavor. If extraparams
    is specified, it must be a dict or something else that can be
    combined with a dict using `update`; it adds additional parameters
    (usually openQA variables) to the POST request. When extraparams
    is used, the BUILD value has '-EXTRA' appended to signify that
    this should not be considered a clean test run for the build.
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
        'VERSION': build.split('-')[1],
        'FLAVOR': flavor,
        'ARCH': arch,
        'BUILD': build,
        'LOCATION': location,
        'CURRREL': currrel,
        'PREVREL': prevrel,
        'SUBVARIANT': subvariant,
        'IMAGETYPE': imagetype
    }
    if extraparams:
        params.update(extraparams)
        # mung the BUILD so this is not considered a 'real' test run
        params['BUILD'] = "{0}-EXTRA".format(params['BUILD'])
    if resultsdb_job_id:
        params['RESULTSDB_JOB_ID'] = resultsdb_job_id

    if arch == 'armhfp':
        params.update({
            'ARCH': 'arm',
            'FAMILY': 'arm',
            # ARM kernel arguments since we are using direct kernel boot
            'APPEND': 'rw root=LABEL=_/ rootwait console=ttyAMA0 console=tty0 consoleblank=0',
        })
    else:
        params['FAMILY'] = 'x86'
    params.update(param_urls)

    # add KERNEL and INITRD arguments when needed
    # TODO: this will not work until https://github.com/os-autoinst/openQA/pull/673 gets merged
    # if 'KERNEL_URL' in params:
    #     params['KERNEL'] = "vmlinuz.{0}".format(build)
    # if 'INITRD_URL' in params:
    #     params['INITRD'] = "initrd.img.{0}".format(build)

    client = OpenQA_Client()

    if not force:
        duplicates = _find_duplicate_jobs(client, param_urls, flavor)
        if duplicates:
            logger.debug("Existing jobs found: %s", ' '.join(str(dupe['id']) for dupe in duplicates))
            return []

    output = client.openqa_request('POST', 'isos', params)
    logger.debug("run_openqa_jobs: executed")
    logger.debug("run_openqa_jobs: planned jobs: %s", output["ids"])

    return output["ids"]


def jobs_from_compose(location, wanted=WANTED, force=False, extraparams=None, create_resultsdb_job=None):
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

    create_resultsdb_job controls whether to create job in ResultsDB for
    this compose.
    """
    location = location.strip('/')
    compose = _get_compose_id(location)
    logger.debug("Finding images for compose %s in location %s", compose, location)
    images = _get_images(location, wanted=wanted)
    if len(images) == 0:
        raise TriggerException("Compose found, but no available images")
    jobs = []
    univs = {}

    # create jobs instance in resultsdb if necessary
    rdb_job_id = None

    if create_resultsdb_job is None:
        create_resultsdb_job = CONFIG.getboolean('report', 'submit_resultsdb')

    if create_resultsdb_job:
        try:
            rdb_instance = ResultsDBapi(CONFIG.get('report', 'resultsdb_url'))
            # add link to page with overall results
            ref_url = "%s/tests/overview?distri=fedora&version=%s&build=%s" % (CONFIG.get('report', 'openqa_url'),
                                                                               compose.split('-')[-2], compose)
            job = rdb_instance.create_job(ref_url=ref_url, name=compose)
            rdb_job_id = job["id"]
        except ResultsDBapiException as e:
            logger.error(e)

    # schedule per-image jobs, keeping track of the highest score
    # per arch along the way
    for (flavor, arch, score, param_urls, subvariant, imagetype) in images:
        jobs.extend(run_openqa_jobs(param_urls, flavor, arch, subvariant, imagetype, compose,
                                    location, force=force, extraparams=extraparams,
                                    resultsdb_job_id=rdb_job_id))
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
                                        compose, location, force=force, extraparams=extraparams,
                                        resultsdb_job_id=rdb_job_id))

    return (compose, jobs)
