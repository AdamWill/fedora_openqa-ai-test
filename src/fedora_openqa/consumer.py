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
            return self._consume_compose(message.body)
        elif 'coreos' in message.topic:
            return self._consume_fcosbuild(message.body)
        elif 'odcs' in message.topic:
            return self._consume_odcs(message.body)
        elif 'bodhi.update.status.testing' in message.topic:
            # from Bodhi 8.0 onwards, this message should always and
            # only be published when we want to run tests:
            return self._consume_update(message.body, force=True)

    def _check_mainline(self, body):
        """
        Given a message containing the standard Bodhi 'update' dict,
        decide whether it's for mainline Fedora or ELN, or not. We
        have to do this on a couple of paths, so share the code.
        """
        reldict = body.get("update", {}).get('release', {})
        if reldict.get('id_prefix') != 'FEDORA' or reldict.get('name') == 'ELN':
            advisory = body.get("update", {}).get('alias')
            self.logger.debug("%s doesn't look like a mainline Fedora update, no jobs scheduled", advisory)
            return False
        return True

    # pylint: disable=too-many-arguments
    def _update_schedule(self, advisory, version, flavors, force=True, updic=None):
        """
        Shared schedule, log, return code for _handle_retrigger and
        _consume_update.
        """
        jobs = []
        # pylint: disable=no-member
        for arch in self.update_arches:
            jobs.extend(
                schedule.jobs_from_update(
                    advisory,
                    version,
                    flavors=flavors,
                    openqa_hostname=self.openqa_hostname,
                    force=force,
                    arch=arch,
                    updic=updic
                )
            )
        if jobs:
            self.logger.info("openQA jobs run on update %s: "
                      "%s", advisory, ' '.join(str(job) for job in jobs))
        else:   # pragma: no cover
            if force:
                self.logger.warning("No openQA jobs run!")
            else:
                self.logger.debug("No openQA jobs run, likely already tested")

    def _compose_schedule(self, location, description):
        """Shared schedule, log, return code for _consume_compose and
        _consume_odcs.
        """
        self.logger.info("Scheduling openQA jobs for compose %s", description)
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

    def _consume_compose(self, body):
        """Consume a 'compose' type message."""
        status = body.get('status')
        location = body.get('location')
        compstr = body.get('compose_id', location)

        if 'FINISHED' in status and location:
            # We have a complete pungi4 compose
            self._compose_schedule(location, compstr)

    def _consume_fcosbuild(self, body):
        """Consume an FCOS build state change message."""
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

    def _consume_odcs(self, body):
        """Consume an ODCS compose state change message."""
        # this is intentionally written to blow up if required info is
        # missing from the message, as that would likely indicate a
        # message format change and we'd need to handle that
        if body["compose"]["state"] != 2:
            self.logger.debug("Not a 'finished success' message, ignoring")
            return
        if body["event"] != "state-changed":
            self.logger.debug("Not a state change message, ignoring")
            return
        cid = body["compose"].get("pungi_compose_id") or ""
        if not cid.startswith("Fedora-ELN"):
            self.logger.debug("Not an ELN compose, ignoring")
            return
        url = body["compose"]["toplevel_url"]
        desc = f"{cid} at {url}"
        self._compose_schedule(url, desc)

    def _consume_update(self, body, force=True):
        """
        Given a message containing an "update" dict, decide whether
        we should schedule tests for it and for what flavors, then
        hand off scheduling to _update_schedule.
        """
        update = body.get("update", {})
        advisory = update.get("alias")
        reldict = update.get("release", {})
        version = reldict.get("version")
        if not self._check_mainline(body) or not advisory or not version:
            return
        # list of flavors to run the tests for, starts empty
        flavors = []

        # check the list of non-critpath packages we test
        self.logger.debug("Checking non-critpath test list for update %s", advisory)
        flavors.extend(schedule.get_testlist_flavors(update))

        # get the critpath flavors
        cpflavors = schedule.get_critpath_flavors(update)
        if cpflavors or (update.get("critpath") and not update.get("critpath_groups")):
            self.logger.info("Scheduling openQA jobs for critical path update %s", advisory)
            if cpflavors:
                flavors.extend(cpflavors)
            else:
                # if we know update is critpath but we don't know the
                # groups, schedule all flavors
                flavors = None

        if flavors == []:
            # This means we ain't running nothin'
            self.logger.debug("Update is not critical path and no packages in test list, no jobs scheduled")
            return

        if flavors:
            # let's remove dupes
            flavors = set(flavors)
            tmpl = "Running update tests for flavors %s for update %s"
            self.logger.info(tmpl, ', '.join(flavors), advisory)
        self._update_schedule(advisory, version, flavors, force=force, updic=update)


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
    ResultsDB when a job completes or is restarted.
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
            newjobs = list(body["result"].values())
        else:
            newjobs = [body["id"]]
        self.logger.info("reporting results for %s", ", ".join(str(job) for job in newjobs))
        # pylint: disable=no-member
        report.resultsdb_report(
            resultsdb_url=self.resultsdb_url, jobs=newjobs, do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)

# vim: set textwidth=120 ts=8 et sw=4:
