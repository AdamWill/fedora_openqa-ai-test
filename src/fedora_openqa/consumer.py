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
import fedora_messaging.config
from openqa_client.client import OpenQA_Client

# internal imports
from .config import UPDATETL
from . import schedule
from . import report


def _find_true_body(message):
    """Currently the ZMQ->AMQP bridge produces a message with the
    entire fedmsg as the 'body'. When the publisher is converted to
    AMQP it will likely only include the 'msg' dict as the 'body'. So
    let's try and make sure we work either way...
    https://github.com/fedora-infra/fedmsg-migration-tools/issues/20
    """
    body = message.body
    if 'msg' in body and 'msg_id' in body:
        # OK, pretty sure this is a translated fedmsg, take 'msg'
        body = body['msg']
    return body

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
        """Consume incoming message."""
        if 'pungi' in message.topic:
            return self._consume_compose(message)
        elif 'coreos' in message.topic:
            return self._consume_fcosbuild(message)
        elif 'bodhi.update.status.testing' in message.topic:
            return self._consume_retrigger(message)
        elif 'bodhi' in message.topic:
            return self._consume_update(message)

    def _consume_compose(self, message):
        """Consume a 'compose' type message."""
        body = _find_true_body(message)
        status = body.get('status')
        location = body.get('location')
        compstr = body.get('compose_id', location)
        # don't schedule tests on modular composes, for now, as we know
        # many fail
        if 'Fedora-Modular' in compstr:
            self.logger.info("Not scheduling jobs for modular compose %s", compstr)
            return

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
                return

            self.logger.debug("Finished")
            return

        return

    def _consume_fcosbuild(self, message):
        """Consume an FCOS build state change message."""
        body = _find_true_body(message)
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
            return
        self.logger.debug("Finished")
        return

    def _update_schedule(self, advisory, version, flavors):
        """
        Shared schedule, log, return code for _consume_retrigger and
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
                openqa_hostname=self.openqa_hostname, force=True, arch=arch))
        if jobs:
            self.logger.info("openQA jobs run on update %s: "
                      "%s", advisory, ' '.join(str(job) for job in jobs))
        else:
            self.logger.warning("No openQA jobs run!")
            return

        self.logger.debug("Finished")

    def _consume_retrigger(self, message):
        """Consume a 're-trigger tests' type message."""
        body = _find_true_body(message)
        if not body.get("re-trigger"):
            self.logger.debug("Not a re-trigger request, ignoring")
            return
        advisory = body.get("artifact", {}).get("id", "")
        self.logger.info("Handling test re-trigger request for update %s", advisory)
        if not advisory.startswith("FEDORA-2"):
            self.logger.info("Update %s does not look like a Fedora package update, ignoring", advisory)
            return
        # there's an extra weird UUID string on the end of the update
        # ID in these messages for some reason, split it off
        advisory = "-".join(advisory.split("-")[0:3])
        # we get the 'dist tag' as the 'version' here, need to trim
        # the leading "f"
        version = body.get("artifact", {}).get("release", "")[1:]
        # these messages do not include critpath status, so we can't
        # "decide" whether to test the update. instead, as they're
        # re-trigger messages, we'll just see whether we already
        # tested the update, and for what flavors if so, and re-test
        # in that same context
        client = OpenQA_Client(self.openqa_hostname)
        build = f"Update-{advisory}"
        existjobs = client.openqa_request("GET", "jobs", params={"build": build})["jobs"]
        flavors = [job.get("settings", {}).get("FLAVOR", "") for job in existjobs]
        # strip the updates- prefix and ignore empty strings
        flavors = [flavor.split("updates-")[-1] for flavor in flavors if flavor]
        flavors = set(flavors)
        if flavors:
            self.logger.info("Re-running tests for update %s, flavors %s", advisory, ", ".join(flavors))
            self._update_schedule(advisory, version, flavors)
        else:
            self.logger.info("No existing jobs found, so not scheduling any!")

    def _consume_update(self, message):
        """Consume an 'update' type message."""
        body = _find_true_body(message)
        update = body.get('update', {})
        advisory = update.get('alias')
        critpath = update.get('critpath', False)
        version = update.get('release', {}).get('version')
        # to make sure this is a Fedora, not EPEL, update
        idpref = update.get('release', {}).get('id_prefix')
        # list of flavors to run the tests for, starts empty. If set
        # to None, means 'run all tests'.
        flavors = []

        # if update is critpath, always run all update tests
        if critpath and advisory and version and idpref == 'FEDORA':
            self.logger.info("Scheduling openQA jobs for critical path update %s", advisory)
            flavors = None

        # otherwise check the list of non-critpath packages we test
        elif advisory and version and idpref == 'FEDORA':
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
        self._update_schedule(advisory, version, flavors)


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
        body = _find_true_body(message)
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
        body = _find_true_body(message)
        job = body['id']
        self.logger.info("reporting results for %s", job)
        # pylint: disable=no-member
        report.resultsdb_report(
            resultsdb_url=self.resultsdb_url, jobs=[job], do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)

# vim: set textwidth=120 ts=8 et sw=4:
