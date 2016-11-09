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
import re
import copy
import time
import logging
from operator import attrgetter

# External dependencies
import mwclient.errors
from openqa_client.client import OpenQA_Client
from resultsdb_api import ResultsDBapi, ResultsDBapiException
from wikitcms.wiki import Wiki, ResTuple

# Internal dependencies
import fedora_openqa_schedule.conf_test_suites as conf_test_suites
from fedora_openqa_schedule.config import CONFIG

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
    flavor = job['settings']['FLAVOR']
    fs = job['settings']['TEST'].split('_')[-1]
    desktop = job['settings'].get('DESKTOP', '')
    try:
        (subvariant, imagetype, _) = flavor.split('-')
    except ValueError:
        # the above fails when the flavor is 'universal'. This is just
        # to avoid crashing, these values should never be used
        subvariant = imagetype = 'universal'
    imagetype = imagetype.replace('boot', 'netinst')
    # reverse the - to _ sub we do when constructing the flavor (we
    # know no type values really have _ in them, so this is safe)
    imagetype = imagetype.replace('_', '-')
    subvariant = subvariant.replace('_Base', '')
    subvariant_or_arm = "ARM" if arch == "arm" else subvariant
    if 'UEFI' in job['settings']:
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
    tsname = job['settings']['TEST']
    # There usually ought to be an entry in TESTSUITES for all
    # tests, but just in case someone messed up, let's be safe
    if tsname not in conf_test_suites.TESTSUITES:
        logger.warning("No TESTSUITES entry found for test {0}!".format(tsname))
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

    else: # isdict - this is the simple list case.
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
                if not testcase in conf_test_suites.TESTCASES:
                    logger.warning("No TESTCASES entry found for {0}!".format(testcase))
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


def wiki_report(wiki_url, jobs=None, build=None, do_report=None):
    """Report results from openQA jobs to Wikitcms. Either jobs (an
    iterable of job IDs) or build (an openQA BUILD string, usually a
    Fedora compose ID) is required (if neither is specified, the
    openQA client will raise TypeError). If do_report is False, will
    just print out the python-wikitcms ResTups for inspection. If
    do_report is None, will read the setting from the config file; if
    no config file is present, default is True.
    """
    client = OpenQA_Client()
    jobs = client.get_jobs(jobs=jobs, build=build)
    passed_testcases = get_passed_testcases(jobs, client)
    logger.info("passed testcases: %s", passed_testcases)
    if do_report is None:
        do_report = CONFIG.getboolean('report', 'submit_wiki')

    if do_report:
        logger.info("reporting test passes")
        wiki = Wiki(('https', wiki_url), '/w/')
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


def resultsdb_report(resultsdb_url, jobs=None, build=None, resultsdb_job_id=None, do_report=None):
    """Report results from openQA jobs to ResultsDB. Either jobs (an
    iterable of job IDs) or build (an openQA BUILD string, usually a
    Fedora compose ID) is required (if neither is specified, the
    openQA client will raise TypeError). If set, report jobs to ResultsDB
    job, specified by resultsdb_job_id. If not set, try to obtain ID from
    openQA job settings. If do_report is False, will
    just print out list of jobs to report for inspection. If
    do_report is None, will read the setting from the config file; if
    no config file is present, default is True.
    """
    if do_report is None:
        do_report = CONFIG.getboolean('report', 'submit_resultsdb')

    if do_report:
        try:
            rdb_instance = ResultsDBapi(resultsdb_url)
        except ResultsDBapiException as e:
            logger.error(e)
            return

    client = OpenQA_Client()
    jobs = client.get_jobs(jobs=jobs, build=build)

    tcname_safeify = re.compile(r"\W+")  # allow only words to be used in testcase name

    for job in jobs:
        # ResultsDB's job_id must be set in argument or during test scheduling so we know what job to report to
        rdb_job_id = resultsdb_job_id if resultsdb_job_id else job['settings'].get('RESULTSDB_JOB_ID', None)
        if not rdb_job_id:
            logger.warning("Job %s doesn't have ResultsDB job ID in settings nor was it set by CLI argument", job['id'])
            continue
        testsuite = job['settings']['TEST']
        if testsuite not in conf_test_suites.TESTSUITES:
            logger.warning("No TESTSUITES entry found for test {0}!".format(testsuite))
            continue
        # map openQA's result to ResultsDB's result
        rdb_result = {'passed': "PASSED", 'failed': "FAILED"}.get(job['result'], 'NEEDS_INSPECTION')
        for testcase in conf_test_suites.TESTSUITES[testsuite]:
            # create dot-separated and safe name from testcase name from wiki
            tc_name = tcname_safeify.sub("_", testcase).lower()
            tc_name = tc_name[len("qa_testcase_"):] if tc_name.startswith("qa_testcase_") else tc_name
            tc_name = "openqa.%s.%s" % (conf_test_suites.TESTCASES[testcase]['type'].lower(), tc_name)

            # append all extra data that could be useful
            extradata = {}
            extradata['arch'] = job['settings'].get('ARCH', None)
            extradata['firmware'] = 'uefi' if 'UEFI' in job['settings'] else 'bios'
            extradata['item'] = job['settings'].get('BUILD', None)
            extradata['type'] = "compose"
            extradata['subvariant'] = job['settings'].get('SUBVARIANT', None)
            extradata['imagetype'] = job['settings'].get('IMAGETYPE', None)
            # append all additional data
            if testcase in conf_test_suites.TESTCASES_RESULTSDB_EXTRADATA:
                extradata.update(_uniqueres_replacements(job, conf_test_suites.TESTCASES_RESULTSDB_EXTRADATA[testcase]))

            # create link back to openQA testrun
            job_url = "%s/tests/%s" % (CONFIG.get('report', 'openqa_url'), job['id'])
            # create link to testcase page on Fedora wiki
            testcase_url = "%s/%s" % (CONFIG.get('report', 'wiki_url'), testcase)

            logger.info("ResultsDB: %s, %s, %s, %s", rdb_job_id, tc_name, rdb_result, extradata)
            if do_report:
                rdb_instance.create_result(rdb_job_id, tc_name, rdb_result, log_url=job_url, **extradata)
                # this updates testcase link in ResultsDB with every POST. otherwise we would check whether
                # this testcase exists in ResultsDB and update link if needed, but it would actually take more
                # requests than this solution
                rdb_instance.update_testcase(tc_name, testcase_url)
