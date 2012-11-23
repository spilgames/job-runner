from django.test import TestCase
from django.utils import timezone

from job_runner.apps.job_runner.models import Run


class RunManagerTestCase(TestCase):
    """
    Tests for the job run manager.
    """
    fixtures = ['test_job']

    def test_awaiting_enqueue(self):
        """
        Test :meth:`.Run.awaiting_enqueue`.
        """
        self.assertEqual(
            1, Run.objects.awaiting_enqueue().filter(job_id=1).count())

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.save()

        self.assertEqual(
            0, Run.objects.awaiting_enqueue().filter(job_id=1).count())
