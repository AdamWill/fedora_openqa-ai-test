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
import fedfind.release
import wikitcms.wiki
from openqa_client.client import OpenQA_Client
from six.moves import configparser
from six.moves.urllib.request import urlopen


# Internal dependencies
from fedora_openqa_schedule.config import CONFIG

logger = logging.getLogger(__name__)


class TriggerException(Exception):
    pass


class WaitError(Exception):
    """Raised when we waited for something too long."""
    pass


def download_image(image, iso_path=None):
    """Download a given image with a name that should be unique,
    optionally specifying destination directory.
    Returns the filename of the image (not the path).
    """
    # if no iso_path is specified, parse it from config file
    if not iso_path:
        iso_path = CONFIG.get('schedule', 'iso-path')
    ver = image.version.replace(' ', '_')
    if image.imagetype == 'boot':
        isoname = "{0}_{1}_{2}_boot.iso".format(ver, image.payload, image.arch)
    else:
        isoname = "{0}_{1}".format(ver, image.filename)
    filename = os.path.join(iso_path, isoname)
    if not os.path.isfile(filename):
        # adapted from the University of StackOverflow:
        # https://stackoverflow.com/questions/22676
        resp = urlopen(image.url)
        meta = resp.info()
        size = int(meta.getheaders("Content-Length")[0]) // (1024 * 1024)
        logger.info("downloading %s (%s) to %s, %sMiB", image.url, image.desc, filename, size)
        fout = open(filename, 'wb')
        while True:
            # This is the number of bytes to read between buffer
            # flushes. Value taken from the SO example.
            buffer = resp.read(8192)
            if not buffer:
                break
            fout.write(buffer)
        fout.close()

    else:
        logger.info("%s already exists", filename)
    return isoname


def run_openqa_jobs(isoname, flavor, arch, build, force=False):
    """# run OpenQA 'isos' job on selected isoname, with given arch
    and a version string. **NOTE**: the version passed to OpenQA as
    BUILD and is parsed back into the 'relval report-auto' arguments
    by report_job_results.py; it is expected to be in the form of a
    3-tuple on which join('_') has been run, and the three elements
    will be passed as release, compose and milestone. Returns list of
    job IDs. If force is False, jobs will only be scheduled if there
    are no existing, non-cancelled jobs for the same ISO and flavor.
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
        'ISO': isoname,
        'DISTRI': 'fedora',
        'VERSION': build.split('_')[0],
        'FLAVOR': flavor,
        'ARCH': arch,
        'BUILD': build,
        'CURRREL': currrel,
        'PREVREL': prevrel,
    }
    client = OpenQA_Client()
    if not force:
        # Check if we have any existing non-cancelled jobs for this
        # ISO and flavor (checking flavor is important otherwise we'd
        # bail on doing the per-ISO jobs for the ISO we use for the
        # 'universal' tests).
        jobs = client.openqa_request('GET', 'jobs', params={'iso': isoname})['jobs']
        jobs = [job for job in jobs if job['settings']['FLAVOR'] == flavor]
        jobs = [job for job in jobs if
                job.get('state') != 'cancelled' and job.get('result') != 'user_cancelled']
        if jobs:
            logger.info("run_openqa_jobs: Existing jobs found for ISO %s flavor %s, and force "
                        "not set! No jobs scheduled.", isoname, flavor)
            logger.debug("Existing jobs found: %s", ' '.join(str(job['id']) for job in jobs))
            return []

    output = client.openqa_request('POST', 'isos', params)
    logger.debug("run_openqa_jobs: executed")
    logger.debug("run_openqa_jobs: planned jobs: %s", output["ids"])

    return output["ids"]


def jobs_from_current(wiki_url, force=False, arches=None):
    """Schedule jobs against the 'current' release validation event
    (according to wikitcms) if we have not already. Returns the job
    list. If force is False, for each ISO, jobs will only be scheduled
    if there are no existing, non-cancelled jobs for the same ISO and
    flavor. If not set, load list of arches from config file.
    """
    # if arches weren't specified as argument, parse them from config file
    if not arches:
        arches = re.split(r'\W+', CONFIG.get('schedule', 'arches').strip())

    wiki = wikitcms.wiki.Wiki(('https', wiki_url), '/w/')

    currev = wiki.current_event
    logger.info("current event: %s", currev.version)

    jobs = _jobs_from_fedfind(currev.ff_release, arches=arches, force=force)
    logger.info("jobs_from_current: planned jobs: %s", ' '.join(str(j) for j in jobs))

    build = '_'.join((currev.ff_release.release, currev.ff_release.milestone, currev.ff_release.compose))
    return (build, jobs)


def jobs_from_compose(release='', milestone='', compose='', arches=None, force=False, wait=None):
    """Schedule jobs against a specific release/compose. Returns the
    list of job IDs.

    'release', 'milestone' and 'compose' identify a release according
    to fedfind conventions (e.g. '23', 'Beta', 'TC2' or '24',
    'Branched', '20160301'). A ValueError may be raised (by fedfind)
    if there is something wrong with these values.

    arches may be an iterable of arches to run on. If not specified,
    the default from config file will be used.

    If force is False, for each ISO, jobs will only be scheduled if
    there are no existing, non-cancelled jobs for the same ISO and
    flavor.

    'wait' is a number of minutes to wait for the compose to appear
    before scheduling the jobs; if None, the value will be read from
    configuration (see config.py for default). Will raise WaitError if
    the compose cannot be found after the wait period. If wait is 0,
    _jobs_from_fedfind will raise TriggerException if the compose does
    not exist.
    """
    # Get the fedfind release object.
    logger.debug("jobs_from_compose: querying fedfind for compose: %s %s %s", release,
                 milestone, compose)
    ff_release = fedfind.release.get_release(release=release, milestone=milestone,
                                             compose=compose)
    logger.info("jobs_from_compose: running on compose: %s", ff_release.version)

    if wait is None:
        wait = CONFIG.getint('schedule', 'compose-wait')
    if wait:
        logger.info("jobs_from_compose: Waiting up to %s mins for compose", str(wait))
        try:
            ff_release.wait(waittime=wait)
        except fedfind.exceptions.WaitError as err:
            raise WaitError(err)

    jobs = _jobs_from_fedfind(ff_release, arches=arches, force=force)
    logger.info("jobs_from_compose: planned jobs: %s", ' '.join(str(j) for j in jobs))

    build = '_'.join((ff_release.release, ff_release.milestone, ff_release.compose))
    return (build, jobs)


def _jobs_from_fedfind(ff_release, force=False, arches=None, imagetypes=None, payloads=None):
    """Given a fedfind.Release object, find the ISOs we want and run
    jobs on them. arches is an iterable of arches to run on, if not
    specified, we'll use value from config file. If force is False,
    for each ISO, jobs will only be scheduled if there are no
    existing, non-cancelled jobs for the same ISO and flavor.
    """
    # if arches, imagetypes or payload weren't specified as argument, parse them from config file
    if not arches:
        # split arches by words (works for both space- and comma-separated values)
        arches = re.split(r'\W+', CONFIG.get('schedule', 'arches').strip())
    if not imagetypes:
        # split imagetypes by words (works for both space- and comma-separated values)
        imagetypes = re.split(r'\W+', CONFIG.get('schedule', 'imagetype').strip())
    if not payloads:
        # split payloads by words (works for both space- and comma-separated values)
        payloads = re.split(r'\W+', CONFIG.get('schedule', 'payload').strip())
    # Find currently-testable images for our arches.
    jobs = []
    queries = (
        fedfind.release.Query('imagetype', imagetypes),
        fedfind.release.Query('arch', arches),
        fedfind.release.Query('payload', payloads))
    logger.debug("querying fedfind for images")
    images = ff_release.find_images(queries)
    # This is kind of icky. The cloud_atomic boot image is the same
    # thing as the cloud_atomic dvd image, so we obviously don't want
    # to get both. Note: we can't use 'netinst' instead of 'boot',
    # because pre-release nightly trees only have 'boot' images, not
    # 'netinst's. And we can't drop 'dvd' because we want the server
    # DVD. There's no really easy way to square this circle until
    # nightly composes look more like real ones.
    images = [img for img in images if not (img.imagetype == 'boot' and img.payload == 'cloud_atomic')]

    if len(images) == 0:
        raise TriggerException("no available images")

    # Now schedule jobs. First, let's get the BUILD value for openQA.
    build = '_'.join((ff_release.release, ff_release.milestone, ff_release.compose))

    # Next let's schedule the 'universal' tests.
    # We have different images in different composes: nightlies only
    # have a generic boot.iso, TC/RC builds have Server netinst/boot
    # and DVD. We always want to run *some* tests -
    # default_boot_and_install at least - for all images we find, then
    # we want to run all the tests that are not image-dependent on
    # just one image. So we have a special 'universal' flavor and
    # product in openQA; all the image-independent test suites run for
    # that product. Here, we find the 'best' image we can for the
    # compose we're running on (a DVD if possible, a boot.iso or
    # netinst if not), and schedule the 'universal' jobs on that
    # image.
    for arch in arches:
        okimgs = (img for img in images if img.arch == arch and
                  any(img.imagetype == okt for okt in ('dvd', 'boot', 'netinst')))
        bestscore = 0
        bestimg = None
        for img in okimgs:
            if img.imagetype == 'dvd':
                score = 10
            else:
                score = 1
            if img.payload == 'generic':
                score += 5
            elif img.payload == 'server':
                score += 3
            elif img.payload == 'workstation':
                score += 1
            if score > bestscore:
                bestimg = img
                bestscore = score
        if not bestimg:
            logger.warn("no universal tests image found for %s", arch)
            continue
        logger.info("running universal tests for %s with %s", arch, bestimg.desc)
        isoname = download_image(bestimg)
        job_ids = run_openqa_jobs(isoname, 'universal', arch, build, force=force)
        jobs.extend(job_ids)

    # Now schedule per-image jobs.
    for image in images:
        isoname = download_image(image)
        flavor = '_'.join((image.payload, image.imagetype))
        job_ids = run_openqa_jobs(isoname, flavor, image.arch, build, force=force)
        jobs.extend(job_ids)
    return jobs
