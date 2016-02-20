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

# Internal dependencies
from fedora_openqa_schedule.config import CONFIG, WANTED

logger = logging.getLogger(__name__)


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


def _get_images(location, wanted=WANTED):
    """Given a Pungi compose top-level location, this returns a set of
    (URL, arch, flavor, score) tuples for images to be tested.
    """
    try:
        resp = urlopen('{0}/metadata/images.json'.format(location))
        metadata = json.load(resp)
    except (ValueError, URLError, HTTPError):
        raise TriggerException("Compose not found, or failed!")
    images = set()
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
                # this is a messy fedfind-lite because productmd does
                # not give us any kind of 'payload' field, we have to
                # sloppily guess it from the filename
                payload = matchdict.pop('payload', '')
                for foundimg in foundimgs:
                    # here's the nice simple 1-to-1 comparison...
                    if not all(item in foundimg.items() for item in matchdict.items()):
                        continue
                    if payload:
                        # here we find the filename, lowercase it, and
                        # split it on '-', and figure the payload will
                        # be one of the elements
                        elems = foundimg['path'].split('/')[-1].lower().split('-')
                        if not payload.lower() in elems:
                            continue

                    # We get here if all match-y stuff passed
                    score = wantimg.get('score', 0)
                    # assign a 'flavor' (another thing productmd ought
                    # to do for us really). if the match dict includes
                    # a payload, use it, otherwise assume the variant
                    # is the payload. add 'type' and 'format', replace
                    # dashes in the values with underscores, join with
                    # dashes.
                    if not payload:
                        payload = variant
                    flavor = [item.replace('-', '_')
                              for item in payload, foundimg['type'], foundimg['format']]
                    flavor = '-'.join(flavor)
                    url = "{0}/{1}".format(location, foundimg['path'])
                    logger.debug("Found image %s for arch %s at %s", flavor, arch, url)
                    images.add((url, flavor, arch, score))
    return images


def run_openqa_jobs(url, flavor, arch, build, force=False):
    """# run OpenQA 'isos' job on ISO at 'url', with given arch
    and a build identifier. **NOTE**: 'build' is passed to openQA as
    BUILD and is later retrieved and parsed by report.py for wiki
    report generation. Returns list of job IDs. If force is False,
    jobs will only be scheduled if there are no existing,
    non-cancelled jobs for the same ISO and flavor.
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
        'ISOURL': url,
        'DISTRI': 'fedora',
        'VERSION': build.split('-')[1],
        'FLAVOR': flavor,
        'ARCH': arch,
        'BUILD': build,
        'CURRREL': currrel,
        'PREVREL': prevrel,
    }
    client = OpenQA_Client()
    if not force:
        isoname = url.split('/')[-1]
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


def jobs_from_compose(location, wanted=WANTED, force=False):
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
    """
    compose = _get_compose_id(location)
    logger.debug("Finding images for compose %s in location %s", compose, location)
    images = _get_images(location, wanted=wanted)
    if len(images) == 0:
        raise TriggerException("Compose found, but no available images")
    jobs = []
    univs = {}

    # schedule per-image jobs, keeping track of the highest score
    # per arch along the way
    for (url, flavor, arch, score) in images:
        jobs.extend(run_openqa_jobs(url, flavor, arch, build=compose, force=force))
        if score > univs.get(arch, 0):
            univs[arch] = url

    # now schedule universal jobs
    for arch in univs.keys():
        logger.info("running universal tests for %s with %s", arch, url)
        jobs.extend(run_openqa_jobs(univs[arch], 'universal', arch, build=compose, force=force))

    return (compose, jobs)
