#!/usr/bin/env python

# Copyright (C) Red Hat Inc.
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
from functools import partial
import logging
import sys

# External dependencies
from resultsdb_api import ResultsDBapiException

# Internal dependencies
from . import schedule
from . import report
from .config import CONFIG

logger = logging.getLogger(__name__)


### SUB-COMMAND METHODS

def command_compose(args):
    """Schedule openQA jobs for a specified compose."""
    extraparams = None
    if args.updates:
        extraparams = {'GRUBADD': "inst.updates={0}".format(args.updates)}
    flavors = None
    if args.flavors:
        flavors = args.flavors.split(',')
    arches = None
    if args.arches:
        arches = args.arches.split(',')
    try:
        (_, jobs) = schedule.jobs_from_compose(
            args.location, force=args.force, extraparams=extraparams,
            openqa_hostname=args.openqa_hostname, arches=arches, flavors=flavors)
    except schedule.TriggerException as err:
        logger.warning("No jobs run! %s", err)
        sys.exit(1)

    if jobs:
        print("Scheduled jobs: {0}".format(', '.join((str(job) for job in jobs))))
        sys.exit()
    else:
        msg = "No jobs run!"
        if not args.force:
            msg = "{0} {1}".format(
                msg, "You did not pass --force: maybe jobs exist for all ISOs/flavors")
        logger.warning(msg)
        sys.exit(1)

    logger.debug("finished")
    sys.exit()


def command_update_task(args):
    """Schedule openQA jobs for a specified update or task."""
    flavors = []
    if args.flavor:
        flavors = [args.flavor]
    if hasattr(args, 'task'):
        if not args.task.isdigit():
            logger.error("Koji task ID must be all digits!")
            sys.exit(1)
        buildarg = args.task
    else:
        buildarg = args.update
    jobs = schedule.jobs_from_update(buildarg, args.release, flavors=flavors, force=args.force,
                                     openqa_hostname=args.openqa_hostname, arch=args.arch)
    print("Scheduled jobs: {0}".format(', '.join((str(job) for job in jobs))))
    sys.exit()

def command_report(args):
    """Map a list of openQA job IDs and/or builds to Wikitcms test
    results, and either display the ResTups for inspection or report
    the results to the wiki and/or ResultsDB.
    """
    jobs = [int(job) for job in args.jobs if job.isdigit()]
    builds = [build for build in args.jobs if not build.isdigit()]

    openqa_args = {
        'openqa_hostname': args.openqa_hostname,
        'openqa_baseurl': args.openqa_baseurl
    }
    # to avoid a bunch of boiler plate below, let's use some partials
    wikireport = partial(report.wiki_report, wiki_hostname=args.wiki_hostname, **openqa_args)
    rdbreport = partial(report.resultsdb_report, resultsdb_url=args.resultsdb_url, **openqa_args)
    if jobs:
        try:
            if args.wiki:
                wikireport(jobs=jobs, do_report=True)
            if args.resultsdb:
                rdbreport(jobs=jobs, do_report=True)
            if not args.wiki and not args.resultsdb:
                # use wiki_report to only print results
                wikireport(jobs=jobs, do_report=False)
        except (report.LoginError, ResultsDBapiException) as e:
            logger.error("Reporting failed: %s", e)
    if builds:
        for build in builds:
            try:
                if args.wiki:
                    wikireport(build=build, do_report=True)
                if args.resultsdb:
                    rdbreport(build=build, do_report=True)
                if not args.wiki and not args.resultsdb:
                    # use wiki_report to only print results
                    wikireport(build=build, do_report=False)
            except (report.LoginError, ResultsDBapiException) as e:
                logger.error("Reporting failed: %s", e)


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

    args.func(args)


def parse_args(args=None):
    """Parse arguments with argparse. Args can be passed in for
    testing as args; usually, will parse sys.argv.
    """
    parser = argparse.ArgumentParser(description=(
        "Run OpenQA tests for a release validation test event."))
    subparsers = parser.add_subparsers()

    parser_compose = subparsers.add_parser('compose', description="Schedule jobs for a specific compose.")
    parser_compose.add_argument(
        'location', help="The URL of the compose (for Pungi 4 composes, the /compose directory)",
        metavar="COMPOSE_URL")
    parser_compose.add_argument(
        '--openqa-hostname', help="openQA host to schedule jobs on (default: client library "
        "default)", metavar='HOSTNAME')
    parser_compose.add_argument(
        '--force', '-f', help="For each ISO/flavor combination, schedule jobs even if there "
        "are existing, non-cancelled jobs for that combination", action='store_true')
    parser_compose.add_argument(
        '--updates', '-u', help="URL to an updates image to load for all tests. The tests that "
        "test updates image loading will fail when you use this", metavar='UPDATE_IMAGE_URL')
    parser_compose.set_defaults(func=command_compose)
    parser_compose.add_argument(
        "--arches", '-a', help="Comma-separated list of arches to schedule jobs for (if not specified, "
        "all arches will be scheduled)", metavar='ARCHES')
    parser_compose.add_argument(
        "--flavors", help="Comma-separated list of flavors to schedule jobs for (if not specified, "
        "all flavors will be scheduled)", metavar='FLAVORS')

    # parser_update and parser_task are nearly the same, so...
    parser_update = subparsers.add_parser('update', description="Schedule jobs for a specific update.")
    parser_update.add_argument('update', help="The update ID (e.g. 'FEDORA-2017-b07d628952')", metavar='UPDATE')
    parser_task = subparsers.add_parser('task', description="Schedule jobs for a specific Koji task.")
    parser_task.add_argument('task', help="The task ID (e.g. '32099714')", metavar='TASK')
    for updtaskparser in [parser_update, parser_task]:
        if updtaskparser is parser_update:
            targetstr = 'update'
        else:
            targetstr = 'task'
        updtaskparser.add_argument('release', help="The release the {0} is for (e.g. '25')".format(targetstr),
                                   type=int, metavar="NN")
        updtaskparser.add_argument('--flavor', help="A single flavor to schedule jobs for (e.g. 'server'), "
                                   "otherwise jobs will be scheduled for all update flavors")
        updtaskparser.add_argument(
            "--openqa-hostname", help="openQA host to schedule jobs on (default: client library "
            "default)", metavar='HOSTNAME')
        updtaskparser.add_argument(
            '--arch', '-a', help="Arch to schedule jobs for (default: x86_64)", metavar='ARCH')
        updtaskparser.add_argument(
            '--force', '-f', help="For each flavor, schedule jobs even if there are existing, non-cancelled jobs "
            "for the {0} for that flavor".format(targetstr), action='store_true')
    parser_update.set_defaults(func=command_update_task)
    parser_task.set_defaults(func=command_update_task)

    parser_report = subparsers.add_parser(
        'report', description="Map openQA job results to Wikitcms test results and either log them to output or "
        "submit them to the wiki and/or ResultsDB.")
    parser_report.add_argument(
        'jobs', nargs='+', help="openQA job IDs or builds (e.g. "
        "'Fedora-24-20160113.n.1'). For each build included, the latest jobs will be reported.")
    parser_report.set_defaults(func=command_report)
    parser_report.add_argument(
        "--openqa-hostname", help="openQA host to query for results (default: client library "
        "default)", metavar='HOSTNAME')
    parser_report.add_argument(
        "--openqa-baseurl", help="Public openQA base URL for producing links to results (default: "
        "client library baseurl, e.g. 'https://openqa.example.org')", metavar='OPENQA_BASEURL')
    parser_report.add_argument(
        "--wiki", action="store_true", default=False, help="Submit results to wiki")
    parser_report.add_argument(
        "--resultsdb", action="store_true", default=False, help="Submit results to ResultsDB")
    parser_report.add_argument(
        "--wiki-hostname", help="Mediawiki host to report to (default: stg.fedoraproject.org). "
        "Scheme 'https' and path '/w/' are currently hard coded", metavar='WIKI_HOSTNAME')
    parser_report.add_argument(
        "--resultsdb-url", help="ResultsDB URL to report to (default: "
        "http://localhost:5001/api/v2.0/)")

    parser.add_argument(
        '--log-file', '-f', help="If given, log into specified file. When not provided, stdout"
        " is used", default=CONFIG.get('cli', 'log-file'))
    parser.add_argument(
        '--log-level', '-l', help="Specify log level to be outputted",
        choices=('debug', 'info', 'warning', 'error', 'critical'),
        default=CONFIG.get('cli', 'log-level'))

    if not args:
        # usual case, use sys.argv
        args = sys.argv[1:]
    return parser.parse_args(args)


def main():
    """Main loop."""
    try:
        run()
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)

if __name__ == '__main__':
    main()

# vim: set textwidth=120 ts=8 et sw=4:
