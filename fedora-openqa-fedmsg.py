#!/usr/bin/env python

# Copyright (C) 2016 John Dulaney
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


"""fedmsg consumer to schedule openQA tests."""


import logging
import re
import sys

import fedmsg
import fedora_openqa_schedule.schedule as schedule


logger = logging.getLogger(__name__)


def consume(msg):
    """Consume incoming message."""
    # two-week atomic messages don't indicate status, so we'll just
    # always run for those, by setting default value 'FINISHED'
    status = msg.get('status', 'FINISHED')
    location = msg.get('location')
    if 'FINISHED' in status and location:
        # We have a complete pungi4 compose or a 2-week atomic compose
        try:
            (compose, jobs) = schedule.jobs_from_compose(location)
        except schedule.TriggerException as err:
            logger.warning("No jobs run! %s", err)
            return 1
        if jobs:
            logger.info("Jobs run on %s: %s", compose, ' '.join(jobs))
        else:
            logger.warning("No jobs run!")
            return 1

        logger.debug("finished")
        return 0

    return 1


def main():
    """Main listener loop."""
    try:
        # catch Pungi 4 'compose status change' messages and old-style
        # two-week Atomic compose 'staging.done' messages, which have
        # the release number in them, so we need a regex
        topicpatt = re.compile(
            r'^org\.fedoraproject\.prod\.(pungi\.compose\.status\.change|'
            'compose\.\d+\.cloudimg-staging\.done)$')
        for (name, endpoint, topic, msg) in fedmsg.tail_messages():
            if topicpatt.match(topic):
                consume(msg)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

