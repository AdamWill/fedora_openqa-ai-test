# Copyright Red Hat, John Dulaney
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
# Author(s): John Dulaney <jdulaney@fedoraproject.org>
#            Adam Williamson <awilliam@redhat.com>

"""fedora-messaging consumers to schedule and report results for
openQA jobs."""

# standard libraries
import logging

# external imports
import fedfind.helpers
import fedora_messaging.config
from openqa_client.client import OpenQA_Client

# internal imports
from .config import UPDATETL
from . import schedule
from . import report

# SCHEDULER


class OpenQAScheduler(object):
    """A fedora-messaging consumer that schedules openQA jobs when a
    new compose or update appears.
    """

    def __init__(self):
        self.openqa_hostname = fedora_messaging.config.conf["consumer_config"]["openqa_hostname"]
        self.update_arches = fedora_messaging.config.conf["consumer_config"]["update_arches"]
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, message):
        """
        Consume incoming message. Note on bodhi.update.status.testing
        vs. update.request.testing: we use both of these to roughly
        mean "a new update showed up". For Rawhide updates,
        status.testing is most reliable, because it is sent for all
        updates as soon as they are created, more or less.
        update.request.testing is not sent at all for Rawhide updates
        bodhi auto-pushes straight to stable. For non-Rawhide updates,
        update.request.testing is usually most reliable, because it is
        sent as soon as the update is created, unless it's somehow
        gated from even being submitted to testing. status.testing is
        only sent after the update has been included in an updates-
        testing push, which may be several hours after it's created.
        So we handle both messages for all updates, with force=False
        so we'll run the tests only for whichever one we see first.
        """
        if 'pungi' in message.topic:
            return self._consume_compose(message)
        elif 'coreos' in message.topic:
            return self._consume_fcosbuild(message)
        elif 'bodhi.update.status.testing' in message.topic:
            return self._consume_ready(message)
        elif 'bodhi.update.edit' in message.topic:
            # we always want to run tests when an update is edited,
            # even if they already ran
            return self._consume_update(message, force=True)
        elif 'bodhi' in message.topic:
            return self._consume_update(message, force=False)

    def _check_mainline(self, message):
        """
        Given a message containing the standard Bodhi 'update' dict,
        decide whether it's for mainline Fedora or not. We have to do
        this on a couple of paths, so share the code.
        """
        reldict = message.body.get("update", {}).get('release', {})
        if reldict.get('id_prefix') != 'FEDORA' or reldict.get('name') == 'ELN':
            advisory = message.body.get("update", {}).get('alias')
            self.logger.debug("%s doesn't look like a mainline Fedora update, no jobs scheduled", advisory)
            return False
        return True

    def _update_schedule(self, advisory, version, flavors, force=True):
        """
        Shared schedule, log, return code for _handle_retrigger and
        _consume_update.
        """
        # flavors
        # being None here results in our desired behaviour (jobs will
        # be created for *all* flavors)
        jobs = []
        # pylint: disable=no-member
        for arch in self.update_arches:
            jobs.extend(schedule.jobs_from_update(
                advisory, version, flavors=flavors,
                openqa_hostname=self.openqa_hostname, force=force, arch=arch))
        if jobs:
            self.logger.info("openQA jobs run on update %s: "
                      "%s", advisory, ' '.join(str(job) for job in jobs))
        else:
            if force:
                self.logger.warning("No openQA jobs run!")
            else:
                self.logger.debug("No openQA jobs run, likely already tested")

    def _handle_retrigger(self, body):
        """
        Handle re-trigger request messages. These are published
        when someone clicks the Re-Trigger Tests button in Bodhi.
        Rather than re-deciding what tests to run, we'll see whether
        we already tested the update, and for what flavors if so, and
        re-test in that same context.
        """
        update = body.get("update", {})
        advisory = update.get('alias')
        version = update.get('release', {}).get('version')
        if not advisory or not version:
            self.logger.warning("Unable to find advisory or version, no jobs scheduled!")
            return
        client = OpenQA_Client(self.openqa_hostname)
        build = f"Update-{advisory}"
        existjobs = client.openqa_request("GET", "jobs", params={"build": build})["jobs"]
        flavors = [job.get("settings", {}).get("FLAVOR", "") for job in existjobs]
        # strip the updates- prefix and ignore empty strings
        flavors = [flavor.split("updates-")[-1] for flavor in flavors if flavor]
        flavors = set(flavors)
        if flavors:
            self.logger.info("Re-running tests for update %s, flavors %s", advisory, ", ".join(flavors))
            self._update_schedule(advisory, version, flavors, force=True)
        else:
            self.logger.info("No existing jobs found, so not scheduling any!")

    def _consume_compose(self, message):
        """Consume a 'compose' type message."""
        body = message.body
        status = body.get('status')
        location = body.get('location')
        compstr = body.get('compose_id', location)

        if 'FINISHED' in status and location:
            # We have a complete pungi4 compose
            self.logger.info("Scheduling openQA jobs for compose %s", compstr)
            try:
                # pylint: disable=no-member
                (compose, jobs) = schedule.jobs_from_compose(location, openqa_hostname=self.openqa_hostname)
            except schedule.TriggerException as err:
                self.logger.warning("No openQA jobs run! %s", err)
                return
            if jobs:
                self.logger.info("openQA jobs run on compose %s: "
                          "%s", compose, ' '.join(str(job) for job in jobs))
            else:
                self.logger.warning("No openQA jobs run!")

    def _consume_fcosbuild(self, message):
        """Consume an FCOS build state change message."""
        body = message.body
        # this is intentionally written to blow up if required info is
        # missing from the message, as that would likely indicate a
        # message format change and we'd need to handle that
        if body["state"] != "FINISHED" or body["result"] != "SUCCESS":
            self.logger.debug("Not a 'finished success' message, ignoring")
            return
        builddir = body["build_dir"]
        self.logger.info("Scheduling openQA jobs for FCOS build %s", builddir)
        jobs = schedule.jobs_from_fcosbuild(builddir, openqa_hostname=self.openqa_hostname)
        if jobs:
            self.logger.info("openQA jobs run: %s", ' '.join(str(job) for job in jobs))
        else:
            self.logger.info("No openQA jobs run!")

    def _consume_ready(self, message):
        """
        Consume a 'ready for testing' type message
        (koji-build-group.build.complete)
        """
        body = message.body
        if not self._check_mainline(message):
            return
        if body.get("re-trigger"):
            return self._handle_retrigger(body)
        # If it's not a re-trigger request, it should be an initial
        # message for a new update. Use force=False to handle races
        # with other messages and not double-schedule new updates
        return self._consume_update(message, force=False)

    def _consume_update(self, message, force=True):
        """
        Given a message containing an "update" dict, decide whether
        we should schedule tests for it and for what flavors, then
        hand off scheduling to _update_schedule.
        """
        update = message.body.get("update", {})
        advisory = update.get('alias')
        critpath = update.get('critpath', False)
        reldict = update.get('release', {})
        version = reldict.get('version')
        # bail if this isn't a mainline Fedora update
        if reldict.get('id_prefix') != 'FEDORA' or reldict.get('name') == 'ELN':
            self.logger.debug("%s doesn't look like a mainline Fedora update, no jobs scheduled", advisory)
            return
        # list of flavors to run the tests for, starts empty. If set
        # to None, means 'run all tests'.
        flavors = []

        # if update is critpath, just let the scheduler handle it
        if critpath and advisory and version:
            self.logger.info("Scheduling openQA jobs for critical path update %s", advisory)
            flavors = None

        # otherwise check the list of non-critpath packages we test
        elif advisory and version:
            self.logger.debug("Checking non-critpath test list for update %s", advisory)
            for build in update.get('builds', []):
                # get just the package name by splitting the NVR. This
                # assumes all NVRs actually contain a V and an R.
                # Happily, RPM rejects dashes in version or release.
                pkgname = build['nvr'].rsplit('-', 2)[0]
                # now check the list and adjust flavors
                if pkgname in UPDATETL:
                    if not UPDATETL[pkgname]:
                        # this means *all* flavors, and we can short
                        self.logger.info("Running ALL openQA tests for update %s", advisory)
                        flavors = None
                        break
                    else:
                        flavors.extend(UPDATETL[pkgname])

        if flavors:
            # let's remove dupes
            flavors = set(flavors)
            # this means we have a list of flavors, not None indicating
            # *all* flavors, let's log that
            tmpl = "Running update tests for flavors %s for update %s"
            self.logger.info(tmpl, ', '.join(flavors), advisory)
        elif flavors == []:
            # This means we ain't running nothin'
            self.logger.debug("Update is not critical path and no packages in test list, no jobs scheduled")
            return

        # Finally, now we've decided on flavors, run the jobs.
        self._update_schedule(advisory, version, flavors, force=force)


# WIKI REPORTER


class OpenQAWikiReporter(object):
    """A fedora-messaging consumer that reports openQA results to
    Wikitcms when a job completes.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.do_report = fedora_messaging.config.conf["consumer_config"]["do_report"]
        self.openqa_hostname = fedora_messaging.config.conf["consumer_config"]["openqa_hostname"]
        self.openqa_baseurl = fedora_messaging.config.conf["consumer_config"]["openqa_baseurl"]
        self.wiki_hostname = fedora_messaging.config.conf["consumer_config"]["wiki_hostname"]

    def __call__(self, message):
        """Consume incoming message."""
        body = message.body
        job = body['id']
        self.logger.info("reporting results for %s", job)
        # pylint: disable=no-member
        results = report.wiki_report(
            wiki_hostname=self.wiki_hostname, jobs=[job], do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)
        if not self.do_report:
            for res in results:
                self.log.info("%s: would report %s", self.__class__.__name__, res)


# RESULTSDB REPORTER


class OpenQAResultsDBReporter(object):
    """A fedora-messaging consumer that reports openQA results to
    ResultsDB when a job completes.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.do_report = fedora_messaging.config.conf["consumer_config"]["do_report"]
        self.openqa_hostname = fedora_messaging.config.conf["consumer_config"]["openqa_hostname"]
        self.openqa_baseurl = fedora_messaging.config.conf["consumer_config"]["openqa_baseurl"]
        self.resultsdb_url = fedora_messaging.config.conf["consumer_config"]["resultsdb_url"]

    def __call__(self, message):
        """Consume incoming message."""
        body = message.body
        if "restart" in message.topic:
            ojob = body["id"]
            job = body["result"][ojob]
        else:
            job = body["id"]
        self.logger.info("reporting results for %s", job)
        # pylint: disable=no-member
        report.resultsdb_report(
            resultsdb_url=self.resultsdb_url, jobs=[job], do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)

# vim: set textwidth=120 ts=8 et sw=4:
