from datetime import datetime, time, timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from job_runner.apps.job_runner.models import (
    Job,
    RescheduleExclude,
    Run,
    Worker,
    WorkerPool,
)


class RunTestCase(TestCase):
    """
    Tests for the job run model.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs'
    ]

    def test_reschedule_after_schedule_dts(self):
        """
        Test reschedule after schedule dts.
        """
        self.assertEqual(1, Run.objects.filter(job_id=1).count())
        Job.objects.get(pk=1).reschedule()
        self.assertEqual(1, Run.objects.filter(job_id=1).count())

        Run.objects.filter(pk=1).update(
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            return_dts=timezone.now()
        )

        Job.objects.get(pk=1).reschedule()
        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.filter(job_id=1).all()
        self.assertEqual(
            runs[0].schedule_dts + timedelta(days=1),
            runs[1].schedule_dts
        )

    def test_reschedule_after_schedule_dts_not_in_past(self):
        """
        Test reschedule after schedule dts is never in the past.
        """
        dts_now = timezone.now()

        Run.objects.filter(pk=1).update(
            schedule_dts=dts_now - timedelta(days=31),
            enqueue_dts=dts_now - timedelta(days=31),
            return_dts=dts_now - timedelta(days=31)
        )

        Job.objects.get(pk=1).reschedule()
        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        run = Run.objects.get(pk=3)
        self.assertEqual(run.schedule_dts, dts_now + timedelta(days=1))

    def test_reschedule_after_complete_dts(self):
        """
        Test reschedule after complete dts.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.save()

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            return_dts=timezone.now()
        )

        job.reschedule()

        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.filter(job_id=1).all()
        self.assertEqual(
            runs[0].return_dts + timedelta(days=1),
            runs[1].schedule_dts
        )

    def test_reschedule_monthly_after_schedule_dts(self):
        """
        Test monthy reschedule after schedule dts.
        """
        in_and_expected = [
            (datetime(2032, 1, 1), datetime(2032, 2, 1)),
            (datetime(2032, 2, 1), datetime(2032, 3, 1)),
            (datetime(2032, 3, 1), datetime(2032, 4, 1)),
            (datetime(2032, 4, 1), datetime(2032, 5, 1)),
            (datetime(2032, 6, 1), datetime(2032, 7, 1)),
            (datetime(2032, 12, 1), datetime(2033, 1, 1)),
        ]

        for in_dts, expected_dts in in_and_expected:

            # if you do not use utc as a timezone here, you get funny results
            # because of day light saving time switching
            in_dts = timezone.make_aware(
                in_dts, timezone.utc)
            expected_dts = timezone.make_aware(
                expected_dts, timezone.utc)

            job = Job.objects.get(pk=1)
            job.reschedule_interval_type = 'MONTH'
            job.save()

            job.run_set.all().delete()

            Run.objects.create(
                job=job,
                schedule_dts=in_dts,
                enqueue_dts=in_dts,
                start_dts=in_dts,
                return_dts=in_dts,
            )

            job.reschedule()
            run = Run.objects.filter(job=1, enqueue_dts__isnull=True)[0]
            self.assertEqual(expected_dts, run.schedule_dts)

    def test_reschedule_with_exclude(self):
        """
        Test reschedule with exclude time.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.reschedule_interval_type = 'HOUR'
        job.save()

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            return_dts=timezone.make_aware(
                datetime(2032, 1, 1, 11, 59), timezone.get_default_timezone())
        )

        RescheduleExclude.objects.create(
            job=job,
            start_time=time(12, 00),
            end_time=time(13, 00),
        )

        job.reschedule()

        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        runs = Run.objects.filter(job_id=1)
        self.assertEqual(
            timezone.make_aware(
                datetime(2032, 1, 1, 13, 59),
                timezone.get_default_timezone()
            ),
            runs[1].schedule_dts
        )

    def test_reschedule_with_invalid_exclude(self):
        """
        Test reschedule with exclude time which is invalid.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_type = 'AFTER_COMPLETE_DTS'
        job.reschedule_interval_type = 'HOUR'
        job.save()

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            return_dts=timezone.make_aware(
                datetime(2012, 1, 1, 11, 59), timezone.get_default_timezone())
        )

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

    def test_reschedule_with_run_scheduled(self):
        """
        Test reschedule when there is already a run scheduled.
        """
        job = Job.objects.get(pk=1)
        self.assertEqual(1, Run.objects.filter(job=job).count())

        Run.objects.filter(pk=1).update(
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            return_dts=timezone.now()
        )

        Run.objects.create(
            job=job,
            schedule_dts=timezone.now()
        )

        self.assertEqual(2, Run.objects.filter(job=job).count())
        job.reschedule()
        self.assertEqual(2, Run.objects.filter(job=job).count())

    def test_reschedule_with_started_run(self):
        """
        Test reschedule when there is already an other started run active.
        """
        job = Job.objects.get(pk=1)
        self.assertEqual(1, Run.objects.filter(job=job).count())

        Run.objects.filter(pk=1).update(
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
            return_dts=timezone.now()
        )

        Run.objects.create(
            job=job,
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
        )

        self.assertEqual(2, Run.objects.filter(job=job).count())
        job.reschedule()
        self.assertEqual(2, Run.objects.filter(job=job).count())

    def test_get_notification_addresses(self):
        """
        Test ``get_notification_addresses`` methods on models.
        """
        self.assertItemsEqual(
            [
                'project1@example.com',
                'pool1@example.com',
                'template1@example.com',
                'job1@example.com',
            ],
            Job.objects.get(pk=1).get_notification_addresses()
        )

    def test_schedule(self):
        """
        Test direct schedule.
        """
        Run.objects.all().delete()

        job = Job.objects.get(pk=1)

        self.assertEqual(0, job.run_set.count())
        job.schedule()
        self.assertEqual(1, job.run_set.count())

    def test_schedule_run_on_all_workers(self):
        """
        Test direct schedule, run on all workers.
        """
        Run.objects.all().delete()

        pool = WorkerPool.objects.get(pk=1)
        pool.workers.add(Worker.objects.get(pk=2))
        pool.save()

        job = Job.objects.get(pk=1)
        job.run_on_all_workers = True
        job.save()

        self.assertEqual(0, job.run_set.count())
        job.schedule()
        self.assertEqual(2, job.run_set.count())
        self.assertEqual(1, Worker.objects.get(pk=1).run_set.count())
        self.assertEqual(1, Worker.objects.get(pk=2).run_set.count())

    def test_schedule_already_scheduled(self):
        """
        Test direct schedule when there is already a scheduled run available.
        """
        job = Job.objects.get(pk=1)
        self.assertEqual(1, job.run_set.count())
        job.schedule()
        self.assertEqual(1, job.run_set.count())
