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

"""report module for fedora-openqa-schedule. Functions related to job
result reporting go here.
"""

# standard libraries
import copy
import time
import logging
from operator import attrgetter

# External dependencies
from openqa_client.client import OpenQA_Client
from wikitcms.wiki import Wiki, ResTuple

# Internal dependencies
import fedora_openqa_schedule.conf_test_suites as conf_test_suites
from fedora_openqa_schedule.config import CONFIG

logger = logging.getLogger(__name__)


class LoginError(Exception):
    """Raised when cannot log in to wiki to submit results."""
    pass


def _uniqueres_replacements(job, uniqueres):
    """Replace some magic values in the 'uniqueres' dict with test job
    properties; this is to distinguish between environments for a test
    case, or tests with the same test case but different test names,
    and so on. Returns nothing because it modifies the uniqueres dict
    in place.
    """
    arch = job['settings']['ARCH']
    flavor = job['settings']['FLAVOR']
    fs = job['settings']['TEST'].split('_')[-1]
    try:
        (subvariant, imagetype, _) = flavor.split('-')
    except ValueError:
        # the above fails when the flavor is 'universal'. This is just
        # to avoid crashing, these values should never be used
        subvariant = imagetype = 'universal'
    imagetype = imagetype.replace('boot', 'netinst')
    subvariant = subvariant.replace('_Base', '')
    if 'UEFI' in job['settings']:
        uefi = 'UEFI'
        bootmethod = 'x86_64 UEFI'
    else:
        uefi = arch
        bootmethod = 'x86_64 BIOS'

    changed = {}
    for key, value in uniqueres.iteritems():
        value = value.replace('$RUNARCH_OR_UEFI$', uefi)
        value = value.replace('$FS$', fs)
        value = value.replace('$RUNARCH$', arch)
        value = value.replace('$BOOTMETHOD$', bootmethod)
        value = value.replace('$SUBVARIANT$', subvariant)
        value = value.replace('$IMAGETYPE$', imagetype)
        changed[key] = value

    return changed


def get_passed_testcases(jobs):
    """Given an iterable of job dicts - any waiting, filtering and so
    on is assumed to have already happened - returns a list of
    wikitcms ResTuples derived from any passed tests.
    """
    passed_testcases = set()
    for job in jobs:
        if job['result'] == 'passed':
            # it's wikitcms' job to take a compose ID and figure out
            # what the validation event for it is.
            composeid = job['settings']['BUILD']
            testsuite = job['settings']['TEST']
            # There usually ought to be an entry in TESTSUITES for all
            # tests, but just in case someone messed up, let's be safe
            if testsuite not in conf_test_suites.TESTSUITES:
                logger.warning("No TESTSUITES entry found for test {0}!".format(testsuite))
                continue
            for testcase in conf_test_suites.TESTSUITES[testsuite]:
                # each 'testsuite' is a list using testcase names to indicate which Wikitcms tests
                # have passed if this job passes. Each testcase name is the name of a dict in the
                # TESTCASES dict-of-dicts which more precisely identifies the 'test instance' (when
                # there is more than one for a testcase) and environment for which the result
                # should be filed. We do a deepcopy here because otherwise the dict in TESTCASES
                # itself is modified in-place and other jobs for the same testcase (but a different
                # environment, section or testname) will read the modified values and be messed up.

                # replace $FOO$ values in uniqueres
                uniqueres = _uniqueres_replacements(job, conf_test_suites.TESTCASES[testcase])
                result = ResTuple(
                    testtype=uniqueres['type'], testcase=testcase,
                    section=uniqueres.get('section'), testname=uniqueres.get('name', ''),
                    env=uniqueres.get('env', ''), status='pass', bot=True, cid=composeid)
                passed_testcases.add(result)

    return sorted(list(passed_testcases), key=attrgetter('testcase'))


def wait_and_report(wiki_url, job_ids=None, build=None, do_report=None, waittime=None):
    """Find some openQA jobs and report the results to Wikitcms (via
    report_results). Either job_ids (an iterable of IDs) or build (an
    openQA BUILD string) is required. wiki_url and do_report are passed to
    report_results and documented there. waittime (int) is how long to
    wait for jobs to complete before giving up; if 'build' is used,
    will also wait for jobs to appear. If jobs are not present and
    complete when waittime expires,
    openqa_client.exceptions.WaitException will be raised. If waittime
    is 0, no waiting is done, and if jobs are not complete, the
    exception will raise immediately.
    """
    if not job_ids and not build:
        raise ValueError("wait_and_report requires either job_ids or build.")

    ret = []
    if waittime is None:
        waittime = CONFIG.getint('report', 'jobs-wait')
    # Use the openQA client lib to wait for jobs to be done. Will
    # raise an openQA client error on wait expiry.
    client = OpenQA_Client()
    # iterate_jobs can work on jobs or build; whichever is set will be used
    for joblist in client.iterate_jobs(jobs=job_ids, build=build, waittime=waittime):
        ret.extend(report_results(joblist, wiki_url, do_report=do_report))
    return ret


def report_results(jobs, wiki_url, do_report=None):
    """Report results from openQA jobs to Wikitcms. jobs is an
    iterable of openQA job dicts. If do_report is False, will just print
    out the python-wikitcms ResTups for inspection. If do_report is None,
    will read the setting from the config file; if no config file is
    present, default is True.
    """
    passed_testcases = get_passed_testcases(jobs)
    logger.info("passed testcases: %s", passed_testcases)
    if do_report is None:
        do_report = CONFIG.getboolean('report', 'submit')

    if do_report:
        logger.info("reporting test passes")
        wiki = Wiki(('https', wiki_url), '/w/')
        if not wiki.logged_in:
            wiki.login()
        if not wiki.logged_in:
            logger.error("could not log in to wiki")
            raise LoginError

        # Submit the results
        (insuffs, dupes) = wiki.report_validation_results(passed_testcases)
        for dupe in dupes:
            tmpl = "already reported result for test %s, env %s! Will not report dupe."
            logger.info(tmpl, dupe.testcase, dupe.env)
        for insuff in insuffs:
            tmpl = "insufficient data for test %s, env %s! Will not report."
            logger.info(tmpl, insuff.testcase, insuff.env)
        return []

    else:
        logger.warning("no reporting is done")
        return passed_testcases
