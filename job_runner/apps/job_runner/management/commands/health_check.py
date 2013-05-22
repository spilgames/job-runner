import json
import logging
import time
from datetime import datetime, timedelta

import zmq
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.utils import timezone

from job_runner.apps.job_runner.models import Worker


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = 'Monitor worker and worker-pool health'

    publisher = None
    """
    Holds the ZMQ ``publisher`` instance, used to publish to the WS server.
    """

    @transaction.commit_manually
    def handle_noargs(self, **options):
        logger.info('Starting health check monitor')
        context = zmq.Context(1)

        # setup the event publisher which is publishing to the WS server
        self.publisher = context.socket(zmq.PUB)
        self.publisher.connect('tcp://{0}:{1}'.format(
            settings.JOB_RUNNER_WS_SERVER_HOSTNAME,
            settings.JOB_RUNNER_WS_SERVER_PORT,
        ))

        # give the subscribers some time to (re-)connect.
        time.sleep(2)

        hc_delta = timedelta(
            seconds=settings.JOB_RUNNER_WORKER_HEALTH_CHECK_INTERVAL)
        next_hc = datetime.utcnow() + hc_delta

        while True:
            if next_hc <= datetime.utcnow():
                self._find_unresponsive_workers_and_mark_runs_as_failed()
                next_hc = datetime.utcnow() + hc_delta
            transaction.commit()
            time.sleep(5)

        self.publisher.close()
        context.term()

    def _find_unresponsive_workers_and_mark_runs_as_failed(self):
        """
        Detect unresponsive workers and mark their active runs as failed.
        """
        logger.info('Looking for unresponsive workers.')
        workers = Worker.objects.all()
        failed_intervals = \
            settings.JOB_RUNNER_WORKER_MARK_JOB_FAILED_AFTER_INTERVALS
        ping_interval = settings.JOB_RUNNER_WORKER_PING_INTERVAL
        ping_margin = settings.JOB_RUNNER_WORKER_PING_MARGIN

        acceptable_delta = timedelta(
            seconds=(failed_intervals * ping_interval) + ping_margin)

        for worker in workers:
            if worker.ping_response_dts + acceptable_delta < timezone.now():
                logger.warning(
                    'Worker ID {0} seems unresponsive.'.format(worker.pk))
                self._mark_worker_runs_as_failed(
                    worker,
                    'Worker does not respond to ping requests.'
                )

    @transaction.commit_manually
    def _mark_worker_runs_as_failed(self, worker, message):
        """
        Mark the runs that are not finished yet as failed for ``worker``.

        :param worker:
            The worker for which to mark the runs as failed.

        :param message:
            A ``str`` containing a message why the runs were marked as failed.

        """
        run_ids = []

        try:
            active_runs = worker.run_set.filter(return_dts__isnull=True)
            active_runs = active_runs.select_for_update()

            for run in active_runs:
                logger.warning('Marking run {0} as failed.'.format(run.pk))
                run.mark_failed(message)
                run_ids.append(run.pk)

        except Exception:
            logger.exception('Something went wrong, rolling back transaction')
            transaction.rollback()
        else:
            transaction.commit()

        # broadcast events after transaction has been comitted :-)
        for run_id in run_ids:
            self.event_publisher.send_multipart([
                'worker.event',
                json.dumps({
                    'event': 'returned',
                    'run_id': run_id,
                    'kind': 'run',
                })
            ])
