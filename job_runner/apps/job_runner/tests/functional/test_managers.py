from django.test import TestCase
from django.utils import timezone

from job_runner.apps.job_runner.models import KillRequest, Run, Worker


class RunManagerTestCase(TestCase):
    """
    Tests for the job run manager.
    """
    fixtures = ['test_jobs']

    def test_scheduled(self):
        """
        Test :meth:`.Run.scheduled`.
        """
        self.assertEqual(
            1, Run.objects.scheduled().filter(job_id=1).count())

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.save()

        self.assertEqual(
            0, Run.objects.scheduled().filter(job_id=1).count())


class KillRequestManagerTestCase(TestCase):
    """
    Tests for the kill-request manager.
    """
    fixtures = ['test_jobs', 'test_workers', 'test_job_templates']

    def test_killable(self):
        """
        Test with one killable run.
        """
        worker = Worker.objects.get(pk=1)
        run = Run.objects.get(pk=1)
        run.start_dts = timezone.now()
        run.pid = 1234
        run.worker = worker
        run.save()

        KillRequest.objects.create(
            run=run,
            schedule_dts=timezone.now(),
        )

        self.assertEqual(1, KillRequest.objects.killable().count())

    def test_killable_run_not_yet_started(self):
        """
        Test when the run has not yet been started.
        """
        KillRequest.objects.create(
            run=Run.objects.get(pk=1),
            schedule_dts=timezone.now(),
        )

        self.assertEqual(0, KillRequest.objects.killable().count())

    def test_killable_run_already_returned(self):
        """
        Test whent he run has already been finished.
        """
        run = Run.objects.get(pk=1)
        run.start_dts = timezone.now()
        run.return_dts = timezone.now()
        run.pid = 1234
        run.save()

        KillRequest.objects.create(
            run=Run.objects.get(pk=1),
            schedule_dts=timezone.now(),
        )

        self.assertEqual(0, KillRequest.objects.killable().count())

    def test_killable_already_in_queue(self):
        """
        Test with one killable run which is already in queue.
        """
        run = Run.objects.get(pk=1)
        run.start_dts = timezone.now()
        run.pid = 1234
        run.save()

        KillRequest.objects.killable().create(
            run=run,
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
        )

        self.assertEqual(0, KillRequest.objects.killable().count())

    def test_killable_already_executed(self):
        """
        Test with one killable run which has been already executed.
        """
        run = Run.objects.get(pk=1)
        run.start_dts = timezone.now()
        run.pid = 1234
        run.save()

        KillRequest.objects.killable().create(
            run=run,
            schedule_dts=timezone.now(),
            execute_dts=timezone.now(),
        )

        self.assertEqual(0, KillRequest.objects.killable().count())
