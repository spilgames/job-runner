import json
import logging
import random
import time
from datetime import datetime, timedelta

import zmq
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import transaction

from job_runner.apps.job_runner.models import KillRequest, Run, Worker


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = 'Broadcast runs and kill-requests to workers'

    publisher = None
    """
    Holds the ZMQ ``publisher`` instance, used to publish to the workers.
    """

    @transaction.commit_manually
    def handle_noargs(self, **options):
        logger.info('Starting queue broadcaster')
        context = zmq.Context(1)

        # setup the publisher to which the workers are subscribing
        self.publisher = context.socket(zmq.PUB)
        self.publisher.bind(
            'tcp://*:{0}'.format(settings.JOB_RUNNER_BROADCASTER_PORT))

        # give the subscribers some time to (re-)connect.
        time.sleep(2)

        ping_delta = timedelta(
            seconds=settings.JOB_RUNNER_WORKER_PING_INTERVAL)
        next_ping_request = datetime.utcnow()

        while True:
            if next_ping_request <= datetime.utcnow():
                self._broadcast_worker_ping()
                next_ping_request = datetime.utcnow() + ping_delta
            self._broadcast_runs()
            self._broadcast_kill_requests()
            transaction.commit()
            time.sleep(5)

        self.publisher.close()
        self.event_publisher.close()
        context.term()

    @transaction.commit_manually
    def _broadcast_runs(self):
        """
        Broadcast runs that are scheduled to run now.

        When the job has ``job__enqueue_is_enabled`` set to ``False``, its
        runs are not broadcasted, unless they are scheduled manually
        (``is_manual`` set to ``True``).

        """
        enqueueable_runs = Run.objects.enqueueable().select_related()

        # Use select_for_update so that the enqueueable runs will be locked.
        # This is to make sure that in case of multiple broadcasters we're not
        # creating any duplicate runs in case of run_on_all_workers=True.
        enqueueable_runs = enqueueable_runs.select_for_update()
        broadcasted = {}
        to_broadcast = []

        try:
            for run in enqueueable_runs:
                # schedule the run if we haven't already scheduled a run for
                # the same job, or when the run.schedule_id is equal to the
                # already scheduled run (which indicates that it needs to be
                # scheduled in parallel).
                if (run.job.pk not in broadcasted or
                        (run.job.pk in broadcasted and
                            broadcasted[run.job.pk] == run.get_schedule_id())):
                    worker = run.worker

                    # reschedule the job (the reschedule method will take care
                    # of checking if we should reschedule the job or not).
                    run.job.reschedule()

                    if not worker:
                        # if the job should run on all workers
                        if run.job.run_on_all_workers:
                            workers = run.job.worker_pool.workers.filter(
                                enqueue_is_enabled=True)
                            if workers.count():
                                broadcasted[run.job.pk] = run.get_schedule_id()

                                for w in workers:
                                    # assign a worker to each run
                                    assigned_run = Run.objects.create(
                                        job=run.job,
                                        schedule_id=run.get_schedule_id(),
                                        worker=w,
                                        schedule_dts=run.schedule_dts,
                                        is_manual=run.is_manual,
                                        schedule_children=run.schedule_children
                                    )
                                    to_broadcast.append((assigned_run, w))

                                # delete the "old" unassigned run
                                run.delete()

                        # select a random worker
                        else:
                            # TODO: take ping response into account?
                            workers = run.job.worker_pool.workers.filter(
                                enqueue_is_enabled=True)
                            if len(workers):
                                # pick a random active worker
                                worker = workers[
                                    random.randint(0, len(workers) - 1)]

                    # this is the case when a run has already a worker assigned
                    # to it, or when we selected a random worker.
                    if worker:
                        to_broadcast.append((run, worker))
                        broadcasted[run.job.pk] = run.get_schedule_id()

        except Exception:
            logger.exception('Something went wrong, rolling back transaction')
            transaction.rollback()
        else:
            transaction.commit()

            for brocast_args in to_broadcast:
                self._broadcast_run(*brocast_args)

    def _broadcast_run(self, run, worker):
        """
        Broadcast ``run`` to ``worker``.
        """
        message = [
            'master.broadcast.{0}'.format(worker.api_key),
            json.dumps({'run_id': run.id, 'action': 'enqueue'})
        ]
        logger.info('Sending: {0}'.format(message))
        self.publisher.send_multipart(message)

    def _broadcast_kill_requests(self):
        """
        Broadcast kill-requests.
        """
        kill_requests = KillRequest.objects.killable().select_related()

        for kill_request in kill_requests:
            run = kill_request.run
            worker = run.worker
            message = [
                'master.broadcast.{0}'.format(worker.api_key),
                json.dumps({
                    'kill_request_id': kill_request.id,
                    'action': 'kill',
                })
            ]
            logger.info('Sending: {0}'.format(message))
            self.publisher.send_multipart(message)

    def _broadcast_worker_ping(self):
        """
        Broadcast ping-request to all the workers.
        """
        workers = Worker.objects.all()

        for worker in workers:
            message = [
                'master.broadcast.{0}'.format(worker.api_key),
                json.dumps({
                    'action': 'ping',
                })
            ]
            logger.debug('Sending: {0}'.format(message))
            self.publisher.send_multipart(message)
