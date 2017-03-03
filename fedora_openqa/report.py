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
import logging
import re
from functools import partial
from operator import attrgetter

# External dependencies
import mwclient.errors
from openqa_client.client import OpenQA_Client
from openqa_client.const import JOB_SCENARIO_WITH_MACHINE_KEYS
from resultsdb_api import ResultsDBapi, ResultsDBapiException
from resultsdb_conventions.fedora import FedoraImageResult, FedoraComposeResult, FedoraBodhiResult
from wikitcms.wiki import Wiki, ResTuple

# Internal dependencies
from . import conf_test_suites
from .config import CONFIG

logger = logging.getLogger(__name__)


class LoginError(Exception):
    """Raised when cannot log in to wiki to submit results."""
    pass


def _uniqueres_replacements(job, tcdict):
    """Replace some magic values in the 'tcdict' dict with test job
    properties; this is to distinguish between environments for a test
    case, or tests with the same test case but different test names,
    and so on. Returns a new dict with the modifications.
    """
    arch = job['settings']['ARCH']
    fs = job['test'].split('_')[-1]
    desktop = job['settings'].get('DESKTOP', '')
    subvariant = job['settings']['SUBVARIANT']
    imagetype = job['settings']['IMAGETYPE']
    imagetype = imagetype.replace('boot', 'netinst')
    subvariant = subvariant.replace('_Base', '')
    subvariant_or_arm = "ARM" if arch == "arm" else subvariant

    if arch == "arm":
        bootmethod = 'ARM'
        firmware = 'ARM'
    elif 'UEFI' in job['settings']:
        firmware = 'UEFI'
        bootmethod = 'x86_64 UEFI'
    else:
        firmware = 'BIOS'
        bootmethod = 'x86_64 BIOS'

    role = ''
    if 'role_deploy_' in job['test']:
        role = job['test'].split('role_deploy_')[1]

    # We effectively deep copy the `tcdict` dict here; if we just modified it directly
    # we'd actually be changing it in TESTCASES, so the results for later jobs in this run
    # with the same testcase (but a different environment, section or testname) would read
    # the modified values and be messed up
    changed = {}
    for key, value in tcdict.iteritems():
        value = value.replace('$FIRMWARE$', firmware)
        value = value.replace('$FS$', fs)
        value = value.replace('$RUNARCH$', arch)
        value = value.replace('$BOOTMETHOD$', bootmethod)
        value = value.replace('$SUBVARIANT$', subvariant)
        value = value.replace('$IMAGETYPE$', imagetype)
        value = value.replace('$DESKTOP$', desktop)
        value = value.replace('$SUBVARIANT_OR_ARM$', subvariant_or_arm)
        value = value.replace('$ROLE$', role)
        changed[key] = value

    return changed


def _get_passed_tcnames(job, composeid, client=None):
    """Given a job dict, find the corresponding entry from TESTSUITES
    and return the test case names that are considered to have passed.
    This is splitting out a chunk of logic from the middle of
    get_passed_testcases to make it shorter and more readable.
    composeid is the compose ID, passed in from get_passed_testcases.
    client can be an OpenQA_Client instance (to save us instantiating
    a new one, and also so checkwiki can use a fake one); it's used
    for entries that use the 'testsuites' condition, we have to go get
    the appropriate results from openQA and check them, we can't
    assume they're already in the jobs list that get_passed_testcases
    got.
    """
    tsname = job['test']
    # There usually ought to be an entry in TESTSUITES for all
    # tests, but just in case someone messed up, let's be safe
    if tsname not in conf_test_suites.TESTSUITES:
        logger.warning("No TESTSUITES entry found for test %s!", tsname)
        return []

    passed = []
    testsuite = conf_test_suites.TESTSUITES[tsname]
    # testsuite can be simply a list of test case names - in which case all those test
    # cases are considered 'passed' if the openQA job overall 'passed' - or a dict whose
    # keys are test case names and whose values are dicts of conditions indicating when
    # that test case should be considered as 'passed'. Here, we handle the conditions for
    # this case. See conf_test_suites for more details.
    isdict = None
    try:
        # check if this is dict case
        testsuite.items()
        isdict = True
    except AttributeError:
        isdict = False
    if isdict:
        # dict case.
        for (testcase, conds) in testsuite.items():
            if not conds:
                # life is easy!
                passed.append(testcase)
                continue

            # otherwise, handle the conditions...
            # modules: the test case is only 'passed' if all listed openQA job modules
            # are present in the job and passed
            if 'modules' in conds:
                tcpass = True
                for modname in conds['modules']:
                    try:
                        # find the matching test module in the job's list (note this
                        # assumes we don't run the same module multiple times, which
                        # is something upstream has recently started allowing...)
                        module = [module for module in job['modules'] if
                                  module['name'] == modname][0]
                        if module.get('result', '') not in ('passed', 'softfailed'):
                            tcpass = False
                            break
                    except IndexError:
                        tcpass = False
                        logger.warning("Did not find module %s in job data!", modname)
                        break
                if not tcpass:
                    # skip to next testsuite item
                    continue

            # test suites: the test case is only 'passed' if there are jobs for all listed
            # test suites for the same build, machine and flavor, and they all passed
            if 'testsuites' in conds:
                if not client:
                    client = OpenQA_Client()
                # Ideally we could query on multiple test names - I'll send a PR for that.
                # As we can't, let's not do multiple single queries, let's just get all
                # results for the same build, machine and flavor and filter ourselves...
                params = {
                    'build': composeid,
                    'machine': job['settings']['MACHINE'],
                    'flavor': job['settings']['FLAVOR'],
                    'latest': 'true',
                }
                candjobs = client.openqa_request('GET', 'jobs', params=params)['jobs']
                _jobs = [_job for _job in candjobs if _job['test'] in conds['testsuites']]
                if len(_jobs) != len(conds['testsuites']):
                    continue
                if any(_job['result'] not in ('passed', 'softfailed') for _job in _jobs):
                    continue

            # we only get here if all the conditions are satisfied
            passed.append(testcase)

    else:  # isdict - this is the simple list case.
        passed = testsuite

    return passed


def get_passed_testcases(jobs, client=None):
    """Given an iterable of job dicts - any waiting, filtering and so
    on is assumed to have already happened - returns a list of
    wikitcms ResTuples derived from any passed tests. client can be an
    OpenQA_Client instance (to save us instantiating a new one, and
    also so checkwiki can use a fake one); it's passed through to
    _get_passed_tcnames, which actually uses it.
    """
    passed_testcases = set()
    for job in jobs:
        if job['result'] in ('passed', 'softfailed'):
            # it's wikitcms' job to take a compose ID and figure out
            # what the validation event for it is.
            composeid = job['settings']['BUILD']
            if composeid.endswith('EXTRA'):
                # this is a 'dirty' test run with extra parameters
                # (usually a test with an updates.img), we never want
                # to report results for these
                logger.debug("Job was run with extra params! Will not report")
                continue
            # find the TESTSUITES entry for the job and parse it to
            # get a list of passed test case names (TESTCASES keys)
            passed = _get_passed_tcnames(job, composeid, client)
            for testcase in passed:
                # skip with warning if testcase is not in TESTCASES
                if testcase not in conf_test_suites.TESTCASES:
                    logger.warning("No TESTCASES entry found for %s!", testcase)
                    continue
                # Each testcase name now in the `passed` list is the name of a dict in the
                # TESTCASES dict-of-dicts which more precisely identifies the 'test instance' (when
                # there is more than one for a testcase) and environment for which the result
                # should be filed.

                # create new dict based on the testcase dict with $FOO$ values replaced
                uniqueres = _uniqueres_replacements(job, conf_test_suites.TESTCASES[testcase])
                result = ResTuple(
                    testtype=uniqueres['type'], testcase=testcase,
                    section=uniqueres.get('section'), testname=uniqueres.get('name', ''),
                    env=uniqueres.get('env', ''), status='pass', bot=True, cid=composeid)
                passed_testcases.add(result)

    return sorted(list(passed_testcases), key=attrgetter('testcase'))


def wiki_report(wiki_hostname=None, jobs=None, build=None, do_report=True, openqa_hostname=None,
                openqa_baseurl=None):
    """Report results from openQA jobs to Wikitcms. Either jobs (an
    iterable of job IDs) or build (an openQA BUILD string, usually a
    Fedora compose ID) is required (if neither is specified, the
    openQA client will raise TypeError). If do_report is False, will
    just print out the python-wikitcms ResTups for inspection.
    """
    client = OpenQA_Client(openqa_hostname)
    # NOTE: `filter_dupes=True` has an odd consequence here. When a
    # job dies and is automatically duplicated, we will try to report
    # a result for the original job, but because of this filter_dupes
    # setting we will actually get the job dict for the clone and try
    # to 'report' that. This is harmless, though, because the clone
    # will still be running and we'll just do nothing (as the result
    # won't be 'passed'). When the clone completes, the consumer will
    # try again and do the right thing.
    jobs = client.get_jobs(jobs=jobs, build=build, filter_dupes=True)

    # cannot do wiki reporting for update jobs
    jobs = [job for job in jobs if 'ADVISORY' not in job['settings']]
    if not jobs:
        logger.debug("No wiki-reportable jobs: most likely all jobs were update tests")
        return []
    passed_testcases = get_passed_testcases(jobs, client)
    logger.info("passed testcases: %s", passed_testcases)

    if not wiki_hostname:
        wiki_hostname = CONFIG.get('report', 'wiki_hostname')

    if do_report:
        logger.info("reporting test passes to %s", wiki_hostname)
        wiki = Wiki(('https', wiki_hostname), '/w/')
        if not wiki.logged_in:
            # This seems to occasionally throw bogus WrongPass errors
            try:
                wiki.login()
            except mwclient.errors.LoginError:
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


def resultsdb_report(resultsdb_url=None, jobs=None, build=None, do_report=True,
                     openqa_hostname=None, openqa_baseurl=None):
    """Report results from openQA jobs to ResultsDB. Either jobs (an
    iterable of job IDs) or build (an openQA BUILD string, usually a
    Fedora compose ID) is required (if neither is specified, the
    openQA client will raise TypeError). If do_report is false-y, will
    just print out list of jobs to report for inspection.
    openqa_hostname is the host name of the openQA server to connect
    to; if set to None, the client library's default behaviour is used
    (see library for more details). openqa_baseurl is the public base
    URL for constructing links to openQA pages; if set to None, the
    OpenQA_Client base_url property (which is derived from the host
    name) will be used.
    """
    if not resultsdb_url:
        resultsdb_url = CONFIG.get('report', 'resultsdb_url')

    if do_report:
        try:
            rdb_instance = ResultsDBapi(resultsdb_url)
        except ResultsDBapiException as e:
            logger.error(e)
            return
    else:
        rdb_instance = None

    client = OpenQA_Client(openqa_hostname)
    if not openqa_baseurl:
        openqa_baseurl = client.baseurl

    # For ResultsDB reporting, we don't want the 'filter_dupes' stuff,
    # which replaces cloned jobs with their clones and only takes the
    # most recent job for each 'scenario' when searching by build. For
    # RDB we just want to forward the results for the exact job IDs we
    # were given, or *all* results for the build, including 'duped'
    # ones. The scenario that's 'harmless' for wiki reporting is not
    # harmless here; if we set True, when a job dies and is cloned,
    # we'll file a bad report due to getting the dict for the clone.
    jobs = client.get_jobs(jobs=jobs, build=build, filter_dupes=False)

    tcname_safeify = re.compile(r"\W+")
    # regex for identifying TEST_TARGET values that suggest an image
    # specific compose test
    image_target_regex = re.compile(r"^(ISO|HDD)(_\d+)?$")

    for job in jobs:
        # don't report jobs that have clone or user-cancelled jobs, or were obsoleted
        if job['clone_id'] is not None or job['result'] == "user_cancelled" or job['result'] == 'obsoleted':
            continue

        try:
            build = job['settings']['BUILD']
            distri = job['settings']['DISTRI']
            version = job['settings']['VERSION']
        except KeyError:
            logger.warning("cannot report job %d because it is missing build/distri/version", job['id'])
            continue

        # sanitize the test name
        tc_name = tcname_safeify.sub("_", job['test']).lower()

        # figure out the resultsdb_convention result type we want and
        # what the 'item' will be, and create a partial for the Result
        # class we want to use with the type-specific args
        ttarget = job['settings'].get('TEST_TARGET', '')
        rdbpartial = None
        if 'ADVISORY' in job['settings']:
            # the 'target' (what will become the 'item' in RDB) is
            # always the update ID for the update test workflow
            rdbpartial = partial(FedoraBodhiResult, job['settings']['ADVISORY'], tc_name='update.' + tc_name)

        elif image_target_regex.match(ttarget):
            # We have a compose test result for a specific image
            # 'build' will be the compose ID, job['settings'][ttarget]
            # will be the filename of the tested image
            imagename = job['settings'][ttarget]
            # special case for images decompressed for testing
            if job['settings']['IMAGETYPE'] == 'raw-xz' and imagename.endswith('.raw'):
                imagename += '.xz'
            rdbpartial = partial(FedoraImageResult, imagename, build, tc_name='compose.' + tc_name)

        elif ttarget == 'COMPOSE':
            # We have a non-image-specific compose test result
            # 'build' will be the compose ID
            rdbpartial = partial(FedoraComposeResult, build, tc_name='compose.' + tc_name)

        # don't report TEST_TARGET=NONE, non-update jobs that are
        # missing TEST_TARGET, or TEST_TARGET values we don't grok
        if ttarget == "NONE":
            # this is an explicit 'do not report' setting, so no warn
            continue
        if not rdbpartial:
            if not ttarget:
                logger.warning("cannot report job %d because TEST_TARGET variable is missing", job['id'])
            else:
                logger.warning("Could not understand TEST_TARGET value %s for job %d", ttarget, job['id'])
            continue

        # construct common args for resultsdb_conventions Result
        kwargs = {}
        # map openQA's results to resultsdb's outcome
        kwargs["outcome"] = {
            'passed': "PASSED",
            'failed': "FAILED",
            'parallel_failed': "FAILED",
            'softfailed': "INFO"
        }.get(job['result'], 'NEEDS_INSPECTION')
        job_url = "%s/tests/%s" % (openqa_baseurl, job['id'])
        if job["result"] in ["passed", "softfailed"]:
            kwargs["tc_url"] = job_url  # point testcase url to latest passed test
        kwargs["ref_url"] = job_url
        kwargs["source"] = "openqa"

        # create link to overall url for group ref_url
        overall_url = "%s/tests/overview?distri=%s&version=%s&build=%s" % (
            openqa_baseurl, distri, version, build)

        # put in the "note" field whether some module failed
        for module in job["modules"]:
            if module["result"] == "failed" and ("fatal" in module["flags"] or "important" in module["flags"]):
                kwargs["note"] = module["name"] + " module failed"
                break
            if module["result"] == "failed" and job["result"] == "softfailed":
                kwargs["note"] = "non-important module {0} failed".format(module["name"])

        # create the Result instance
        rdb_object = rdbpartial(**kwargs)

        # Add some more extradata items
        rdb_object.extradata.update({
            'firmware': 'uefi' if 'UEFI' in job['settings'] else 'bios',
            'arch': job['settings']['ARCH'],
            'scenario': '.'.join(job['settings'][key] for key in JOB_SCENARIO_WITH_MACHINE_KEYS)
        })

        # FIXME: use overall_url as a group ref_url

        rdb_object.report(rdb_instance)

# vim: set textwidth=120 ts=8 et sw=4:
