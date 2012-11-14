from datetime import datetime, time, timedelta

from django.core import mail
from django.test import TestCase

from job_runner.apps.job_runner.models import (
    Job,
    RescheduleExclude,
    Run,
)


class RunTestCase(TestCase):
    """
    Tests for the job run model.
    """
    fixtures = [
        'test_auth',
        'test_project',
        'test_worker',
        'test_job_template',
        'test_job'
    ]

    def test_reschedule_after_schedule_dts(self):
        """
        Test reschedule after schedule dts.
        """
        self.assertEqual(1, Run.objects.filter(job_id=1).count())
        Job.objects.get(pk=1).reschedule()
        self.assertEqual(1, Run.objects.filter(job_id=1).count())

        run = Run.objects.get(pk=1)
        run.enqueue_dts = datetime.utcnow()
        run.return_dts = datetime.utcnow()
        run.save()

        Job.objects.get(pk=1).reschedule()
        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.filter(job_id=1).all()
        self.assertEqual(
            runs[1].schedule_dts + timedelta(days=1),
            runs[0].schedule_dts
        )

    def test_reschedule_after_complete_dts(self):
        """
        Test reschedule after complete dts.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.save()

        run = Run.objects.get(pk=1)
        run.enqueue_dts = datetime.utcnow()
        run.return_dts = datetime.utcnow()
        run.save()

        job.reschedule()

        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.filter(job_id=1).all()
        self.assertEqual(
            runs[1].return_dts + timedelta(days=1),
            runs[0].schedule_dts
        )

    def test_reschedule_with_exclude(self):
        """
        Test reschedule with exclude time.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.reschedule_interval_type = 'HOUR'
        job.save()

        run = Run.objects.get(pk=1)
        run.enqueue_dts = datetime.utcnow()
        run.return_dts = datetime(2012, 1, 1, 11, 59)
        run.save()

        RescheduleExclude.objects.create(
            job=job,
            start_time=time(12, 00),
            end_time=time(13, 00),
        )

        job.reschedule()

        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.all()
        self.assertEqual(datetime(2012, 1, 1, 13, 59), runs[0].schedule_dts)

    def test_reschedule_with_invalid_exclude(self):
        """
        Test reschedule with exclude time which is invalid.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.reschedule_interval_type = 'HOUR'
        job.save()

        run = Run.objects.get(pk=1)
        run.enqueue_dts = datetime.utcnow()
        run.return_dts = datetime(2012, 1, 1, 11, 59)
        run.save()

        RescheduleExclude.objects.create(
            job=job,
            start_time=time(0, 0),
            end_time=time(23, 59),
        )

        job.reschedule()

        self.assertEqual(1, Run.objects.filter(job_id=1).count())
        self.assertTrue(hasattr(mail, 'outbox'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(4, len(mail.outbox[0].to))
        self.assertEqual(
            'Reschedule error for: Test job 1', mail.outbox[0].subject)

    def test_get_notification_addresses(self):
        """
        Test ``get_notification_addresses`` methods on models.
        """
        self.assertEqual(
            sorted([
                'project@example.com',
                'worker@example.com',
                'template@example.com',
                'job@example.com',
            ]),
            sorted(Job.objects.get(pk=1).get_notification_addresses())
        )

    def test_schedule_now(self):
        """
        Test direct schedule.
        """
        Run.objects.all().delete()

        job = Job.objects.get(pk=1)

        self.assertEqual(0, job.run_set.count())
        job.schedule_now()
        self.assertEqual(1, job.run_set.count())
