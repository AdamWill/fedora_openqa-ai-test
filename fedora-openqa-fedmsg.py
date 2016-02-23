#! /usr/bin/python
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


"""fedmsg consumer for fedora-openqa"""


import logging
import fedmsg

import fedora_openqa_schedule.schedule as schedule
import fedora_openqa_schedule.report as report


logger = logging.getLogger(__name__)


def consume(msg):
    """Consume incoming message"""
    status = msg['status']
    location = msg['location']
    if 'FINISHED' in status:
        # We have a complete pungi4 compose!
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
    """Main listener loop"""

    for name, endpoint, topic, msg  in fedmsg.tail_messages():
        if topic == 'org.fedoraproject.prod.pungi.compose.status.change':
            consume(msg)


if __name__ == '__main__':
    main()

