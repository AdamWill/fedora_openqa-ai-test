# Copyright (C) 2016 John Dulaney, Adam Williamson
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

"""fedmsg consumer to schedule openQA jobs."""

import re
import sys

import fedmsg.consumers
import fedora_openqa_schedule.schedule as schedule
import fedora_openqa_schedule.report as report


class OpenQAConsumer(fedmsg.consumers.FedmsgConsumer):
    """A fedmsg consumer that schedules openQA jobs when a new compose
    appears.
    """
    topic = ["org.fedoraproject.prod.pungi.compose.status.change",
             "org.fedoraproject.prod.compose.*"]
    config_key = "fedora_openqa_schedule.consumer.enabled"

    def _log(self, level, message):
        """Convenience function for sticking the class name on the
        front of the log message as an identifier.
        """
        logfnc = getattr(self.log, level)
        logfnc("%s: %s", self.__class__.__name__, message)

    def consume(self, message):
        """Consume incoming message."""
        # as two-week atomic message topics are a bit awkward, we have
        # to do a bit more filtering here
        if not message['topic'] == "org.fedoraproject.prod.pungi.compose.status.change":
            if not message['topic'].endswith(".cloudimg-staging.done"):
                return

        # two-week atomic messages don't indicate status, so we'll just
        # always run for those, by setting default value 'FINISHED'
        status = message['body']['msg'].get('status', 'FINISHED')
        location = message['body']['msg'].get('location')
        compstr = message['body']['msg'].get('compose_id', location)

        if 'FINISHED' in status and location:
            # We have a complete pungi4 compose or a 2-week atomic compose
            self._log('info', "Scheduling openQA jobs for {0}".format(compstr))
            try:
                (compose, jobs) = schedule.jobs_from_compose(location)
            except schedule.TriggerException as err:
                self._log('warning', "No openQA jobs run! {0}".format(err))
                return
            if jobs:
                self._log('warning', "openQA jobs run on %{0}: "
                          "{1}".format(compose, ' '.join(str(job) for job in jobs)))
            else:
                self._log('warning', "No openQA jobs run!")
                return

            self._log('debug', "Finished")
            return

        return


class OpenQAWikiConsumer(fedmsg.consumers.FedmsgConsumer):
    """A fedmsg consumer that reports openQA results to Wikitcms when
    a job completes. This is a parent class for prod, stg and test
    variants, it is not complete in itself. Whichever child you use,
    make sure the openQA client client.conf is pointed at the same
    openQA instance that produces the fedmsgs you're listening for,
    or things will get weird (you'll be getting job IDs from one
    openQA but retrieving the jobs with those same IDs from the other
    openQA).
    """

    def consume(self, message):
        """Consume incoming message."""
        job = message['body']['msg']['id']
        self.log.info("%s: reporting results for %s", self.__class__.__name__, job)
        results = report.wait_and_report(
            self.url, job_ids=[job], do_report=self.report, waittime=0)
        if not self.report:
            for res in results:
                self.log.info("%s: would report %s", self.__class__.__name__, res)


class OpenQAProductionWikiConsumer(OpenQAWikiConsumer):
    """A result reporting consumer that listens for production fedmsgs
    and reports to the production wiki. Only one of these should ever
    be running at one time; it'd be particularly bad if we had two
    running with different FAS accounts, all results would be duped.
    Please don't enable this consumer unless you're sure you know what
    you're doing.
    """
    topic = "org.fedoraproject.prod.openqa.job.done"
    config_key = "fedora_openqa_schedule.wiki.consumer.prod.enabled"
    url = "fedoraproject.org"
    report = True


class OpenQAStagingWikiConsumer(OpenQAWikiConsumer):
    """A result reporting consumer that listens for staging fedmsgs
    and reports to the staging wiki. Only one of these should ever
    be running at one time; it'd be particularly bad if we had two
    running with different FAS accounts, all results would be duped.
    Please don't enable this consumer unless you're sure you know what
    you're doing.
    """
    topic = "org.fedoraproject.stg.openqa.job.done"
    config_key = "fedora_openqa_schedule.wiki.consumer.stg.enabled"
    url = "stg.fedoraproject.org"
    report = True


class OpenQATestWikiConsumer(OpenQAWikiConsumer):
    """A result reporting consumer that listens for dev fedmsgs (so it
    will catch ones produced by fedmsg-dg-replay) and does not really
    report results, it should log the produced ResTuples instead. This
    is the one you should use to test stuff, go nuts with it.
    """
    topic = "org.fedoraproject.dev.openqa.job.done"
    validate_signatures = False
    config_key = "fedora_openqa_schedule.wiki.consumer.test.enabled"
    url = "stg.fedoraproject.org"
    report = False
