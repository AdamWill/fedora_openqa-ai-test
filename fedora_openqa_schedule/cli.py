#!/usr/bin/env python

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

"""CLI module for fedora-openqa-schedule."""

# Standard libraries
import argparse
import logging
import sys

# Internal dependencies
import fedora_openqa_schedule.schedule as schedule
import fedora_openqa_schedule.report as report
from fedora_openqa_schedule.config import CONFIG

logger = logging.getLogger(__name__)

### SUB-COMMAND METHODS

def command_compose(args, wiki_url):
    """run OpenQA on a specified compose, optionally reporting
    results if a matching wikitcms ValidationEvent is found by
    relval/wikitcms.
    """
    extraparams = None
    if args.updates:
        extraparams = {'GRUBADD': "inst.updates={0}".format(args.updates)}
    try:
        (compose, jobs) = schedule.jobs_from_compose(
            args.location, force=args.force, extraparams=extraparams)
    except schedule.TriggerException as err:
        logger.warning("No jobs run! %s", err)
        sys.exit(1)

    if jobs:
        report.wait_and_report(wiki_url, build=compose, do_report=args.submit)
    else:
        msg = "No jobs run!"
        if not args.force:
            msg = "{0} {1}".format(
                msg, "You did not pass --force: maybe jobs exist for all ISOs/flavors")
        logger.warning(msg)
        sys.exit(1)

    logger.debug("finished")
    sys.exit()

def command_report(args, wiki_url):
    """Map a list of openQA job IDs and/or builds to Wikitcms test
    results, and either display the ResTups for inspection or report
    the results to the wiki.
    """
    jobs = [int(job) for job in args.jobs if job.isdigit()]
    builds = [build for build in args.jobs if not build.isdigit()]
    try:
        if jobs:
            report.wait_and_report(
                wiki_url, job_ids=jobs, do_report=args.submit)
        if builds:
            for build in builds:
                report.wait_and_report(
                    wiki_url, build=build, do_report=args.submit)
    except report.LoginError:
        # Module logs for us, no need to dupe it.
        sys.exit(1)

### ARGUMENT PARSING AND SUB-COMMAND INIT

def run():
    """Read in args, set up logging and wikitcms, and run sub-command
    function.
    """
    args = parse_args()
    loglevel = getattr(
        logging, args.log_level.upper(), logging.INFO)
    if args.log_file:
        logging.basicConfig(format="%(levelname)s:%(name)s:%(asctime)s:%(message)s",
                            filename=args.log_file, level=loglevel)
    else:
        logging.basicConfig(level=loglevel)
    # shut up, requests
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

    wiki_url = "fedoraproject.org"
    if args.test:
        logger.debug("using test wiki")
        wiki_url = "stg.fedoraproject.org"

    args.func(args, wiki_url)

def parse_args():
    """Parse arguments with argparse."""
    test_help = "Operate on the staging wiki (for testing)"
    parser = argparse.ArgumentParser(description=(
        "Run OpenQA tests for a release validation test event."))
    subparsers = parser.add_subparsers()

    parser_compose = subparsers.add_parser(
        'compose', description="Run for a specific compose (TC/RC or nightly). If a matching "
        "release validation test event can be found and --submit-results is passed, results "
        "will be reported.")
    parser_compose.add_argument(
        'location', help="The top-level URL of the compose",
        metavar="https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-24-20160113.n.1/compose")
    parser_compose.add_argument(
        '--force', '-f', help="For each ISO/flavor combination, schedule jobs even if there "
        "are existing, non-cancelled jobs for that combination", action='store_true')
    parser_compose.add_argument(
        '--updates', '-u', help="URL to an updates image to load for all tests. The tests that "
        "test updates image loading will fail when you use this")
    parser_compose.set_defaults(func=command_compose)

    parser_report = subparsers.add_parser(
        'report', description="Map openQA job results to Wikitcms test results and optionally "
        "submit them to the wiki.")
    parser_report.add_argument('jobs', nargs='+', help="openQA job IDs or builds (e.g. "
    "'Fedora-24-20160113.n.1'). For each build included, the latest jobs will be reported.")
    parser_report.set_defaults(func=command_report)

    submitgroup = parser.add_mutually_exclusive_group()
    submitgroup.add_argument('--submit', '-s', '--submit-results', action='store_true',
    dest="submit", help="Where appropriate, submit results to the wiki")
    submitgroup.add_argument('--no-submit', '-ns', '--no-submit-results', action='store_false',
    dest="submit", help="Do not submit results to the wiki")
    # This will result in getting the 'submit' value from config file
    # if not explicitly specified, overriding the implied defaults of
    # store_true and store_false
    parser.set_defaults(submit=None)

    parser.add_argument(
        '--test', '-t', help=test_help, action='store_true')
    parser.add_argument(
        '--log-file', '-f', help="If given, log into specified file. When not provided, stdout"
        " is used", default=CONFIG.get('cli', 'log-file'))
    parser.add_argument(
        '--log-level', '-l', help="Specify log level to be outputted",
        choices=('debug', 'info', 'warning', 'error', 'critical'),
        default=CONFIG.get('cli', 'log-level'))

    return parser.parse_args()

def main():
    """Main loop."""
    try:
        run()
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
