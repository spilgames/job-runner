import json
import logging
import time

import zmq
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.utils import timezone

from job_runner.apps.job_runner.models import Job, Run


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

        When the job has ``job__enqueue_is_enabled`` set to ``False``, its
        runs are not broadcasted, unless they are scheduled manually
        (``is_manual`` set to ``True``).

        :param publisher:
            A ``zmq`` publisher.

        """
        active_jobs = Job.objects.filter(
            run__enqueue_dts__isnull=False,
            run__return_dts__isnull=True,
        )

        enqueueable_runs = Run.objects.awaiting_enqueue().filter(
            # make sure it should be running now
            schedule_dts__lte=timezone.now(),
        ).exclude(
            # exclude auto scheduled jobs when enqueue is disabled
            job__enqueue_is_enabled=False,
            is_manual=False,
        ).exclude(
            # exclude jobs that are still active
            job__in=active_jobs,
        ).select_related()

        broadcasted_job_ids = []

        for run in enqueueable_runs:
            if run.job.pk not in broadcasted_job_ids:
                worker = run.job.job_template.worker
                message = [
                    'master.broadcast.{0}'.format(worker.api_key),
                    json.dumps({'run_id': run.id, 'action': 'enqueue'})
                ]
                logger.debug('Sending: {0}'.format(message))
                publisher.send_multipart(message)

                # in raw sql, this can be avoided, I couldn't find a way how
                # this can be done with the django orm
                broadcasted_job_ids.append(run.job.pk)
