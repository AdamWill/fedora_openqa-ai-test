# Copyright (C) 2016 John Dulaney, Red Hat Inc.
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

# external imports
import fedmsg.consumers

# internal imports
from .config import CONFIG, UPDATEWL
from . import schedule
from . import report


# COMMON BASE CLASSES WITH OPENQA CONFIG VALUES


class OpenQAProductionConsumer(fedmsg.consumers.FedmsgConsumer):
    """Production mixin for both wiki and ResultsDB reporters so they
    can handily share some config settings.
    """
    topic = "org.fedoraproject.prod.openqa.job.done"

    # Values read from CONFIG are implemented as properties (not class
    # or instance variables) to ease testing
    @property
    def openqa_hostname(self):
        """openQA hostname."""
        return CONFIG.get('consumers', 'prod_oqa_hostname')

    @property
    def openqa_baseurl(self):
        """openQA base URL."""
        return CONFIG.get('consumers', 'prod_oqa_baseurl')


class OpenQAStagingConsumer(fedmsg.consumers.FedmsgConsumer):
    """Staging mixin for both wiki and ResultsDB reporters so they can
    handily share some config settings.
    """
    topic = "org.fedoraproject.stg.openqa.job.done"

    @property
    def openqa_hostname(self):
        """openQA hostname."""
        return CONFIG.get('consumers', 'stg_oqa_hostname')

    @property
    def openqa_baseurl(self):
        """openQA base URL."""
        return CONFIG.get('consumers', 'stg_oqa_baseurl')


class OpenQATestConsumer(fedmsg.consumers.FedmsgConsumer):
    """Test mixin for both wiki and ResultsDB reporters so they can
    handily share some config settings.
    """
    topic = "org.fedoraproject.dev.openqa.job.done"
    validate_signatures = False

    @property
    def openqa_hostname(self):
        """openQA hostname."""
        return CONFIG.get('consumers', 'test_oqa_hostname')

    @property
    def openqa_baseurl(self):
        """openQA base URL."""
        return CONFIG.get('consumers', 'test_oqa_baseurl')


# SCHEDULER CLASSES


class OpenQAScheduler(fedmsg.consumers.FedmsgConsumer):
    """A fedmsg consumer that schedules openQA jobs when a new compose
    or update appears.
    """

    def _log(self, level, message):
        """Convenience function for sticking the class name on the
        front of the log message as an identifier.
        """
        logfnc = getattr(self.log, level)
        logfnc("%s: %s", self.__class__.__name__, message)

    def _consume_compose(self, message):
        """Consume a 'compose' type message."""
        status = message['body']['msg'].get('status')
        location = message['body']['msg'].get('location')
        compstr = message['body']['msg'].get('compose_id', location)
        # don't schedule tests on modular composes, for now, as we know
        # many fail
        if 'Fedora-Modular' in compstr:
            self._log('info', "Not scheduling jobs for modular compose %s", compstr)
            return

        if 'FINISHED' in status and location:
            # We have a complete pungi4 compose
            self._log('info', "Scheduling openQA jobs for compose {0}".format(compstr))
            try:
                # pylint: disable=no-member
                (compose, jobs) = schedule.jobs_from_compose(location, openqa_hostname=self.openqa_hostname)
            except schedule.TriggerException as err:
                self._log('warning', "No openQA jobs run! {0}".format(err))
                return
            if jobs:
                self._log('info', "openQA jobs run on compose {0}: "
                          "{1}".format(compose, ' '.join(str(job) for job in jobs)))
            else:
                self._log('warning', "No openQA jobs run!")
                return

            self._log('debug', "Finished")
            return

        return

    def _consume_update(self, message):
        """Consume an 'update' type message."""
        update = message['body']['msg'].get('update', {})
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
            self._log('info', "Scheduling openQA jobs for critical path update {0}".format(advisory))
            flavors = None

        # otherwise check the whitelist
        elif advisory and version and idpref == 'FEDORA':
            self._log('debug', "Checking whitelist for update {0}".format(advisory))
            for build in update.get('builds', []):
                # get just the package name by splitting the NVR. This
                # assumes all NVRs actually contain a V and an R.
                # Happily, RPM rejects dashes in version or release.
                pkgname = build['nvr'].rsplit('-', 2)[0]
                # now check the whitelist and adjust flavors
                if pkgname in UPDATEWL:
                    if not UPDATEWL[pkgname]:
                        # this means *all* flavors, and we can short
                        self._log('info', "Running ALL openQA tests for whitelisted update {0}".format(advisory))
                        flavors = None
                        break
                    else:
                        flavors.extend(UPDATEWL[pkgname])

        if flavors:
            # this means we have a list of flavors, not None indicating
            # *all* flavors, let's log that
            tmpl = "Running update tests for flavors {0} for whitelisted update {1}"
            self._log('info', tmpl.format(', '.join(flavors), advisory))
        elif flavors == []:
            # This means we ain't running nothin'
            self._log('debug', "Update is not critical path and no packages in whitelist, no jobs scheduled")
            return

        # Finally, now we've decided on flavors, run the jobs. flavors
        # being None here results in our desired behaviour (jobs will
        # be created for *all* flavors)
        # pylint: disable=no-member
        jobs = schedule.jobs_from_update(
            advisory, version, flavors=flavors, openqa_hostname=self.openqa_hostname, force=True)
        if jobs:
            self._log('info', "openQA jobs run on update {0}: "
                      "{1}".format(advisory, ' '.join(str(job) for job in jobs)))
        else:
            self._log('warning', "No openQA jobs run!")
            return

        self._log('debug', "Finished")
        return

    def consume(self, message):
        """Consume incoming message."""
        if 'pungi' in message['body']['topic']:
            return self._consume_compose(message)
        elif 'bodhi' in message['body']['topic']:
            return self._consume_update(message)


class OpenQAProductionScheduler(OpenQAScheduler, OpenQAProductionConsumer):
    """A scheduling consumer that listens for production fedmsgs and
    creates events in the production openQA instance by default.
    """
    topic = ["org.fedoraproject.prod.pungi.compose.status.change",
             "org.fedoraproject.prod.bodhi.update.request.testing",
             "org.fedoraproject.prod.bodhi.update.edit"]
    config_key = "fedora_openqa.scheduler.prod.enabled"


class OpenQAStagingScheduler(OpenQAScheduler, OpenQAStagingConsumer):
    """A scheduling consumer that listens for staging fedmsgs and
    creates events in the staging openQA instance by default.
    """
    topic = ["org.fedoraproject.stg.pungi.compose.status.change",
             "org.fedoraproject.stg.bodhi.update.request.testing",
             "org.fedoraproject.stg.bodhi.update.edit"]
    config_key = "fedora_openqa.scheduler.stg.enabled"


class OpenQATestScheduler(OpenQAScheduler):
    """A scheduling consumer that listens for dev fedmsgs and creates
    events in a local openQA instance by default.
    """
    topic = ["org.fedoraproject.dev.pungi.compose.status.change",
             "org.fedoraproject.dev.bodhi.update.request.testing",
             "org.fedoraproject.dev.bodhi.update.edit"]
    config_key = "fedora_openqa.scheduler.test.enabled"
    # We just hardcode this here and don't inherit from TestConsumer,
    # as the config values are intended for the Reporter consumers
    # that *consume* openQA jobs, we likely always want localhost for
    # test *creating* openQA jobs
    openqa_hostname = 'localhost'


# WIKI REPORTER CLASSES


class OpenQAWikiReporter(fedmsg.consumers.FedmsgConsumer):
    """A fedmsg consumer that reports openQA results to Wikitcms when
    a job completes. This is a parent class for prod, stg and test
    variants, it is not intended to be used itself.
    """

    def consume(self, message):
        """Consume incoming message."""
        job = message['body']['msg']['id']
        self.log.info("%s: reporting results for %s", self.__class__.__name__, job)
        # pylint: disable=no-member
        results = report.wiki_report(
            wiki_hostname=self.wiki_hostname, jobs=[job], do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)
        if not self.do_report:
            for res in results:
                self.log.info("%s: would report %s", self.__class__.__name__, res)


class OpenQAProductionWikiReporter(OpenQAWikiReporter, OpenQAProductionConsumer):
    """A result reporting consumer that listens for production fedmsgs
    and reports to the production wiki. Only one of these should ever
    be running at one time; it'd be particularly bad if we had two
    running with different FAS accounts, all results would be duped.
    Please don't enable this consumer unless you're sure you know what
    you're doing.
    """
    config_key = "fedora_openqa.reporter.wiki.prod.enabled"

    @property
    def wiki_hostname(self):
        """Wiki hostname."""
        return CONFIG.get('consumers', 'prod_wiki_hostname')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'prod_wiki_report')


class OpenQAStagingWikiReporter(OpenQAWikiReporter, OpenQAStagingConsumer):
    """A result reporting consumer that listens for staging fedmsgs
    and reports to the staging wiki. Only one of these should ever
    be running at one time; it'd be particularly bad if we had two
    running with different FAS accounts, all results would be duped.
    Please don't enable this consumer unless you're sure you know what
    you're doing.
    """
    config_key = "fedora_openqa.reporter.wiki.stg.enabled"

    @property
    def wiki_hostname(self):
        """Wiki hostname."""
        return CONFIG.get('consumers', 'stg_wiki_hostname')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'stg_wiki_report')


class OpenQATestWikiReporter(OpenQAWikiReporter, OpenQATestConsumer):
    """A result reporting consumer that listens for dev fedmsgs (so it
    will catch ones produced by fedmsg-dg-replay) and does not really
    report results, it should log the produced ResTuples instead. This
    is the one you should use to test stuff, go nuts with it.
    """
    config_key = "fedora_openqa.reporter.wiki.test.enabled"

    @property
    def wiki_hostname(self):
        """Wiki hostname."""
        return CONFIG.get('consumers', 'test_wiki_hostname')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'test_wiki_report')


# RESULTSDB REPORTER CLASSES


class OpenQAResultsDBReporter(fedmsg.consumers.FedmsgConsumer):
    """A fedmsg consumer that reports openQA results to ResultsDB when
    a job completes. This is a parent class for prod and test
    variants, it is not complete in itself.
    """

    def consume(self, message):
        """Consume incoming message."""
        job = message['body']['msg']['id']
        self.log.info("%s: reporting results for %s", self.__class__.__name__, job)
        # pylint: disable=no-member
        report.resultsdb_report(
            resultsdb_url=self.resultsdb_url, jobs=[job], do_report=self.do_report,
            openqa_hostname=self.openqa_hostname, openqa_baseurl=self.openqa_baseurl)


class OpenQAProductionResultsDBReporter(OpenQAResultsDBReporter, OpenQAProductionConsumer):
    """A result reporting consumer that listens for production fedmsgs.
    By default it reports to localhost; please don't configure it to
    report to the official ResultsDB instances unless you're sure you
    know what you're doing.
    """
    config_key = "fedora_openqa.reporter.resultsdb.prod.enabled"

    @property
    def resultsdb_url(self):
        """ResultsDB URL."""
        return CONFIG.get('consumers', 'prod_rdb_url')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'prod_rdb_report')


class OpenQAStagingResultsDBReporter(OpenQAResultsDBReporter, OpenQAStagingConsumer):
    """A result reporting consumer that listens for staging fedmsgs.
By default it reports to localhost; please don't configure it to
    report to the official ResultsDB instances unless you're sure you
    know what you're doing.
    """
    config_key = "fedora_openqa.reporter.resultsdb.stg.enabled"

    @property
    def resultsdb_url(self):
        """ResultsDB URL."""
        return CONFIG.get('consumers', 'stg_rdb_url')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'stg_rdb_report')


class OpenQATestResultsDBReporter(OpenQAResultsDBReporter, OpenQATestConsumer):
    """A result reporting consumer that listens for dev fedmsgs (so it
    will catch ones produced by fedmsg-dg-replay) and reports to a
    ResultsDB instance running on localhost:5001 (as you get by running
    the development mode).
    """
    config_key = "fedora_openqa.reporter.resultsdb.test.enabled"

    @property
    def resultsdb_url(self):
        """ResultsDB URL."""
        return CONFIG.get('consumers', 'test_rdb_url')

    @property
    def do_report(self):
        """Whether to report."""
        return CONFIG.getboolean('consumers', 'test_rdb_report')

# vim: set textwidth=120 ts=8 et sw=4:
