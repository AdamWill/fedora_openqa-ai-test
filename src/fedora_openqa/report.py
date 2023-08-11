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

"""report module for fedora-openqa-schedule. Functions related to job
result reporting go here.
"""

# standard libraries
import logging
import re
import time
from functools import partial
from operator import attrgetter

# External dependencies
import mwclient.errors
from openqa_client.client import OpenQA_Client
from openqa_client.const import JOB_SCENARIO_WITH_MACHINE_KEYS
from resultsdb_api import ResultsDBapi, ResultsDBapiException, ResultsDBAuth
from resultsdb_conventions.fedora import FedoraImageResult, FedoraComposeResult, FedoraBodhiResult
from resultsdb_conventions.fedoracoreos import FedoraCoreOSBuildResult, FedoraCoreOSImageResult
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
    subvariant_or_local = "Local" if "Cloud" in subvariant else subvariant
    cloud_or_base = "Cloud" if "Cloud" in subvariant else "Base"
    if arch == "aarch64":
        bootmethod = "aarch64"
        firmware = "UEFI"
    elif 'UEFI' in job['settings']:
        firmware = 'UEFI'
        bootmethod = 'x86_64 UEFI'
    else:
        firmware = 'BIOS'
        bootmethod = 'x86_64 BIOS'
    # desktop apps: the test suite names the app, the matrix has
    # descriptions like "file manager". so we need to map
    apps = {
        "evince": "document viewer",
        "gnome_text_editor": "text editor",
        "eog": "image viewer",
        "desktop_terminal": "terminal emulator",
        "nautilus": "file manager",
        "help_viewer": "help viewer",
    }
    app = apps.get(job["test"], "")
    ipaorad = "FreeIPA"
    if job['test'].endswith("_ad"):
        ipaorad = "Active Directory"

    # We effectively deep copy the `tcdict` dict here; if we just modified it directly
    # we'd actually be changing it in TESTCASES, so the results for later jobs in this run
    # with the same testcase (but a different environment, section or testname) would read
    # the modified values and be messed up
    changed = {}
    for key, value in tcdict.items():
        value = value.replace('$FIRMWARE$', firmware)
        value = value.replace('$FS$', fs)
        value = value.replace('$RUNARCH$', arch)
        value = value.replace('$BOOTMETHOD$', bootmethod)
        value = value.replace('$SUBVARIANT$', subvariant)
        value = value.replace('$IMAGETYPE$', imagetype)
        value = value.replace('$DESKTOP$', desktop)
        value = value.replace('$SUBVARIANT_OR_LOCAL$', subvariant_or_local)
        value = value.replace('$CLOUD_OR_BASE$', cloud_or_base)
        value = value.replace('$APP$', app)
        value = value.replace('$FREEIPA_OR_AD$', ipaorad)
        changed[key] = value

    return changed


def _get_passed_tcnames(job, result, composeid, client=None):
    """Given a job dict, find the corresponding entry from TESTSUITES
    and return the test case names that are considered to have passed.
    This is splitting out a chunk of logic from the middle of
    get_passed_testcases to make it shorter and more readable. result
    is the overall result of the job: usually only pass or softfail
    jobs will generate any passed test cases, but one special case of
    the 'modules' condition allows even an overall-failed job to
    generate passed test cases if a particular module passed.
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
                if result in ('passed', 'softfailed'):
                    passed.append(testcase)
                continue

            # otherwise, handle the conditions...
            # modules: the test case is 'passed' if all listed openQA job modules
            # are present in the job and passed, the overall job result *is not
            # considered*. we allow this to be combined with a 'testsuites'
            # conditional by altering 'result' here.
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
                        if modname == 'workstation_core_applications':
                            if job['settings'].get("DESKTOP") == 'kde':
                                # this is a known and OK case, no warning
                                break
                        logger.warning("Did not find module %s in job data!", modname)
                        break
                if tcpass:
                    # overwrite overall job result with 'passed'
                    result = 'passed'
                else:
                    # we cannot possibly get a pass now, so skip to next
                    # testsuite item
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
                    'latest': '1',
                }
                candjobs = client.openqa_request('GET', 'jobs', params=params)['jobs']
                _jobs = [_job for _job in candjobs if _job['test'] in conds['testsuites']]
                if len(_jobs) != len(conds['testsuites']):
                    continue
                if any(_job['result'] not in ('passed', 'softfailed') for _job in _jobs):
                    continue

            # we only get here if all the conditions are satisfied,
            # now we check result, which is either the overall job
            # result that we were passed or 'passed' if a 'modules'
            # condition was present and satisfied
            if result in ('passed', 'softfailed'):
                passed.append(testcase)

    # other side of 'isdict' condition - this is the simple list case.
    elif result in ('passed', 'softfailed'):
        passed = testsuite
        # special case: for install_default_upload on Workstation or
        # Silverblue, add base_initial_setup (#100)
        if job["settings"]["SUBVARIANT"] in ("Silverblue", "Workstation") and tsname == "install_default_upload":
            passed.append("QA:Testcase_base_initial_setup")

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
        # it's wikitcms' job to take a compose ID and figure out
        # what the validation event for it is.
        composeid = job['settings']['BUILD']
        if composeid.endswith('EXTRA') or composeid.endswith('NOREPORT'):
            # this is a 'dirty' test run with extra parameters
            # (usually a test with an updates.img) or some kind
            # of throwaway run, we never want to report results
            # for these
            logger.debug("Job %d is a NOREPORT job or was run with extra params! Will not report", job['id'])
            continue
        # find the TESTSUITES entry for the job and parse it to
        # get a list of passed test case names (TESTCASES keys)
        passed = _get_passed_tcnames(job, job['result'], composeid, client)
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
            # IoT events only have a "General" test type and don't
            # need to worry about sections, so hardcode that. env
            # is always the arch
            if job["settings"]["BUILD"].startswith("Fedora-IoT"):
                uniqueres["type"] = "General"
                uniqueres["section"] = ""
                uniqueres["env"] = job["settings"]["ARCH"]
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
    if not jobs:
        logger.debug("wiki_report: No jobs found!")
        return []

    # cannot do wiki reporting for update jobs
    jobs = [job for job in jobs if 'ADVISORY' not in job['settings'] and 'KOJITASK' not in job['settings']]
    if not jobs:
        logger.debug("wiki_report: All jobs were update or Koji task jobs, no wiki reporting possible!")
        return []
    # there are no CoreOS or ELN wiki validation events, currently
    jobs = [
        job for job in jobs
        if "coreos" not in job['settings'].get("SUBVARIANT", "").lower()
        and job['settings']['VERSION'] != "ELN"
    ]
    if not jobs:
        logger.debug("wiki_report: All jobs were CoreOS, update or Koji task jobs, no wiki reporting possible!")
        return []
    passed_testcases = get_passed_testcases(jobs, client)
    logger.info("passed testcases: %s", passed_testcases)

    if not wiki_hostname:
        wiki_hostname = CONFIG.get('report', 'wiki_hostname')

    if do_report:
        logger.info("reporting test passes to %s", wiki_hostname)
        wiki = Wiki(wiki_hostname, max_retries=40)
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
            logger.debug("full ResTuple: %s", dupe)
        for insuff in insuffs:
            tmpl = "insufficient data for test %s, env %s! Will not report."
            logger.info(tmpl, insuff.testcase, insuff.env)
            logger.debug("full ResTuple: %s", insuff)
        return []

    else:
        logger.warning("no reporting is done")
        return passed_testcases

def sanitize_tcname(tcname):
    """Replace non-alphanumeric characters in a test case name with
    underscores and lower-cases the whole thing. Used for the name as
    reported to ResultsDB. Split out into a function so it can be
    shared with check_compose, which needs to take a test case name
    from a ResultsDB report and find a matching openQA job.
    """
    return re.sub(r"\W+", "_", tcname).lower()

def get_scenario_string(job):
    """Produce a string representation of the job's scenario (omitting
    keys we don't want to use in our particular situation). Split out
    into a function for sharing with check_compose, which needs to
    take a scenario string from a ResultsDB report and find a matching
    openQA job (with all the corresponding keys).
    """
    scenkeys = [key for key in JOB_SCENARIO_WITH_MACHINE_KEYS if key not in ('VERSION', 'TEST')]
    return '.'.join(job['settings'][key] for key in scenkeys)

def resultsdb_report(resultsdb_url=None, jobs=None, build=None, do_report=True,
                     openqa_hostname=None, openqa_baseurl=None, err_raise=True):
    """Report results from openQA jobs to ResultsDB. Either jobs (an
    iterable of job IDs) or build (an openQA BUILD string, usually a
    Fedora compose ID or Fedora CoreOS version) is required (if neither
    is specified, the openQA client will raise TypeError). If do_report
    is false-y, will just print out list of jobs to report for
    inspection.
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
        authmethod = None
        authuser = CONFIG.get("report", "resultsdb_user")
        authpass = CONFIG.get("report", "resultsdb_password")
        if authuser and authpass:
            authmethod = ResultsDBAuth.basic_auth(authuser, authpass)
        try:
            rdb_instance = ResultsDBapi(resultsdb_url, request_auth=authmethod)
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

    # regex for identifying TEST_TARGET values that suggest an image
    # specific compose test
    image_target_regex = re.compile(r"^(ISO|HDD)(_\d+)?$")

    # children of failed jobs that we want to report after we're done
    kids = []
    # this will be the last error we encountered in the parent run
    err = None

    for (idx, job) in enumerate(jobs, start=1):
        # drop job from kids so we don't double-report
        if job['id'] in kids:
            kids.remove(job['id'])
        # don't report jobs that have clone or user-cancelled jobs, or were obsoleted
        if job['clone_id'] is not None or job['result'] == "user_cancelled" or job['result'] == 'obsoleted':
            continue
        # don't report Koji 'task' tests (usually scratch build tests),
        # at least for now, we don't have a convention for it
        if 'KOJITASK' in job['settings']:
            continue

        try:
            build = job['settings']['BUILD']
            distri = job['settings']['DISTRI']
            version = job['settings']['VERSION']
        except KeyError:
            logger.warning("cannot report job %d because it is missing build/distri/version", job['id'])
            continue

        if build.endswith('EXTRA') or build.endswith('NOREPORT'):
            # this is a 'dirty' test run with extra parameters
            # (usually a test with an updates.img) or some kind
            # of throwaway run, we never want to report results
            # for these
            logger.debug("Job %d is a NOREPORT job or was run with extra params! Will not report", job['id'])
            continue

        # derive some CoreOS-specific values if appropriate
        if job["settings"].get("SUBVARIANT", "").lower() == "coreos":
            # FIXME: this is hacky, should do it better
            form = job["settings"]["FLAVOR"].split("-")[-1]
            # https://docs.fedoraproject.org/en-US/fedora-coreos/faq/#_what_is_the_format_of_the_version_number
            # FIXME: maybe pass this in at creation?
            streams = {
                "1": "next",
                "2": "testing",
                "3": "stable"
            }
            stream = streams.get(build.split(".")[2], "unknown")

        # sanitize the test name
        tc_name = sanitize_tcname(job['test'])

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
            imagename = job['settings'].get(ttarget)
            if not imagename:
                # this should never happen, but it *can* if someone
                # messes up the templates or a job clone. like me.
                logger.warning("cannot report job %d because variable TEST_TARGET points to is missing", job['id'])
                continue
            # special case for images decompressed for testing
            if job['settings']['IMAGETYPE'] == 'raw-xz' and imagename.endswith('.raw'):
                imagename += '.xz'
            if job["settings"].get("SUBVARIANT", "").lower() == "coreos":
                rdbpartial = partial(
                    FedoraCoreOSImageResult,
                    platform="metal",
                    filename=imagename,
                    form=form,
                    arch=job["settings"]["ARCH"],
                    build=build,
                    stream=stream,
                    tc_name='fcosbuild.' + tc_name
                )
            else:
                locator = build
                # special case: for ELN, the locator needs to be the compose URL
                if version == "ELN":
                    locator = job["settings"]["LOCATION"]
                rdbpartial = partial(FedoraImageResult, imagename, locator, tc_name='compose.' + tc_name)

        elif ttarget == 'COMPOSE':
            # We have a non-image-specific compose test result
            # 'build' will be the compose ID
            if job["settings"].get("SUBVARIANT", "").lower() == "coreos":
                rdbpartial = partial(FedoraCoreOSBuildResult, build, stream, tc_name='fcosbuild.' + tc_name)
            else:
                locator = build
                # special case: for ELN, the locator needs to be the compose URL
                if version == "ELN":
                    locator = job["settings"]["LOCATION"]
                rdbpartial = partial(FedoraComposeResult, locator, tc_name='compose.' + tc_name)

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
        # map openQA's state/results to resultsdb's outcome
        if job["result"] == "none":
            kwargs["outcome"] = {
                'scheduled': "QUEUED",
                'assigned': "QUEUED",
                'setup': "QUEUED",
                'running': "RUNNING",
                'uploading': "RUNNING"
            }.get(job["state"], "NEEDS_INSPECTION")
        else:
            kwargs["outcome"] = {
                'passed': "PASSED",
                'failed': "FAILED",
                'parallel_failed': "FAILED",
                # we get 'skipped' when a chained parent fails and the
                # child never starts. it seems best to treat this as a
                # failure
                'skipped': "FAILED",
                'softfailed': "INFO",
                'incomplete': "CRASHED",
            }.get(job['result'], 'NEEDS_INSPECTION')
        job_url = "%s/tests/%s" % (openqa_baseurl, job['id'])
        if job["result"] in ["passed", "softfailed"]:
            kwargs["tc_url"] = job_url  # point testcase url to latest passed test
        if job["result"] == "failed":
            # we need to try and file results for children of this job
            # that might have been cancelled with no event emitted:
            # https://pagure.io/fedora-qa/fedora_openqa/issue/107
            kids.extend(
                job.get("children", {}).get("Chained", []) + job.get("children", {}).get("Directly chained", [])
            )
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
        try:
            rdb_object = rdbpartial(**kwargs)
        except ValueError as err:
            # This is fedfind telling us the BUILD value is not a
            # valid compose ID. I should really make this a custom
            # exception...
            if "valid Pungi 4" in str(err):
                logger.warning("resultsdb_report: cannot report for "
                               "%s, not a valid compose ID", build)
                return
            # We didn't find *any* images in the compose, which is
            # odd, but can happen if we try to report a very old
            # result for a compose which has been garbage-collected
            if "Can't find image" in str(err):
                logger.error("fedfind could not find image %s in compose %s",
                             imagename, build)
                return
            # this happens if we try to report results for an old
            # live respin compose for some reason
            if "discovered compose" in str(err) and "does not match" in str(err):
                logger.error("trying to report result for non-current live respin compose, "
                             "this will not work!")
                return
            raise

        # Add some more extradata items
        # for resultsdb purposes we don't want VERSION or TEST in the scenario
        scenkeys = [key for key in JOB_SCENARIO_WITH_MACHINE_KEYS if key not in ('VERSION', 'TEST')]
        rdb_object.extradata.update({
            'firmware': 'uefi' if 'UEFI' in job['settings'] else 'bios',
            'arch': job['settings']['ARCH'],
            'scenario': get_scenario_string(job)
        })

        # FIXME: use overall_url as a group ref_url

        # report result, retrying with a delay on failure
        tries = 40
        while tries:
            try:
                rdb_object.report(rdb_instance)
                err = None
                break
            except Exception as newerr:
                err = newerr
                logger.warning("ResultsDB report failed! Retrying...")
                try:
                    logger.warning("Response: %s", newerr.response)
                    logger.warning("Message: %s", newerr.message)
                except AttributeError:
                    logger.warning("Error: %s", str(newerr))
                tries -= 1
                time.sleep(30)
        if err:
            logger.error("ResultsDB reporting for job %d failed after multiple retries! Giving up.",
                         job['id'])

    if kids:
        resultsdb_report(
            resultsdb_url=resultsdb_url,
            jobs=kids,
            build=build,
            do_report=do_report,
            openqa_hostname=openqa_hostname,
            openqa_baseurl=openqa_baseurl,
            err_raise=False
        )

    if err and err_raise:
        raise err

# vim: set textwidth=120 ts=8 et sw=4:
