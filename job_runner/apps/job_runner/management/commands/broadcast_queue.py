import json
import logging
import time
from datetime import datetime

import zmq
from django.conf import settings
from django.core.management.base import NoArgsCommand

from job_runner.apps.job_runner.models import Run


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = 'Broadcast runs in queue to workers'

    def handle_noargs(self, **options):
        logger.info('Starting queue broadcaster')
        context = zmq.Context(1)
        publisher = context.socket(zmq.PUB)
        publisher.bind(
            'tcp://*:{0}'.format(settings.JOB_RUNNER_BROADCASTER_PORT))

        # give the subscribers some time to (re-)connect.
        time.sleep(2)

        while True:
            self._broadcast(publisher)
            time.sleep(5)

        publisher.close()
        context.term()

    def _broadcast(self, publisher):
        """
        Broadcast runs that are scheduled to run now.

        :param publisher:
            A ``zmq`` publisher.

        """
        enqueueable_runs = Run.objects.awaiting_enqueue().filter(
            schedule_dts__lte=datetime.utcnow()).select_related()

        for run in enqueueable_runs:
            worker = run.job.job_template.worker
            message = [
                'master.broadcast.{0}'.format(worker.api_key),
                json.dumps({'run_id': run.id, 'action': 'enqueue'})
            ]
            logger.debug('Sending: {0}'.format(message))
            publisher.send_multipart(message)
