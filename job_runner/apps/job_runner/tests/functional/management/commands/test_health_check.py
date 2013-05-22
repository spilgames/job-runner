import json
from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from mock import Mock

from job_runner.apps.job_runner.management.commands.health_check import Command
from job_runner.apps.job_runner.models import Run, Worker


class CommandTestCase(TestCase):
    """
    Tests for :class:`.Command`.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test__mark_worker_runs_as_failed(self):
        """
        Test :meth:`.Command._mark_worker_runs_as_failed`.
        """
        worker = Worker.objects.get(pk=1)
        Run.objects.filter(pk=1).update(worker=worker)

        command = Command()
        command.publisher = Mock()

        self.assertEqual(None, Run.objects.get(pk=1).return_dts)

        command._mark_worker_runs_as_failed(worker, 'Test mark as failed')

        run = Run.objects.get(pk=1)
        self.assertNotEqual(None, run.return_dts)
        self.assertFalse(run.return_success)

        command.publisher.send_multipart.assert_called_once_with([
            'worker.event',
            json.dumps({
                'event': 'returned',
                'run_id': 1,
                'kind': 'run',
            })
        ])

    def test__find_unresponsive_workers_and_mark_runs_as_failed(self):
        """
        Test ``_find_unresponsive_workers_and_mark_runs_as_failed``.
        """
        Run.objects.filter(pk=1).update(worker=Worker.objects.get(pk=1))
        Run.objects.filter(pk=2).update(worker=Worker.objects.get(pk=2))

        # In testing.py:
        # JOB_RUNNER_WORKER_PING_INTERVAL = 60 * 5
        # JOB_RUNNER_WORKER_MARK_JOB_FAILED_AFTER_INTERVALS = 3
        acceptable = timezone.now() - timedelta(seconds=(60 * 5 * 3))
        unacceptable = acceptable - timedelta(seconds=15)

        Worker.objects.filter(pk=1).update(ping_response_dts=acceptable)
        Worker.objects.filter(pk=2).update(ping_response_dts=unacceptable)

        command = Command()
        command.publisher = Mock()

        command._find_unresponsive_workers_and_mark_runs_as_failed()

        runs = Run.objects.all()

        # Run pk=1 was marked as failed
        self.assertNotEqual(None, runs[0].return_dts)
        self.assertFalse(runs[0].return_success)

        # Run pk=2 was not touched
        self.assertEqual(None, runs[1].return_success)
        self.assertEqual(None, runs[1].return_dts)

    def test__find_unresponsive_worker_pools(self):
        """
        Test :meth:`.Command._find_unresponsive_worker_pools`.

        In this case, we expect Pool 1 to be responsive and Pool 2 to be
        unresponsive.

        """
        Worker.objects.filter(pk=1).update(ping_response_dts=timezone.now())
        # from settings in ``base.py``:
        # 915 = (60 * 5 * 3) + 15
        Worker.objects.filter(pk=2).update(
            ping_response_dts=timezone.now() - timedelta(seconds=915))

        command = Command()
        command._find_unresponsive_worker_pools()

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(
            'Worker-pool unresponsive: Pool 2', mail.outbox[0].subject)
