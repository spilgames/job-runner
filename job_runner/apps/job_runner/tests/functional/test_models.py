from datetime import datetime, time, timedelta

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from job_runner.apps.job_runner.models import (
    Job,
    RescheduleExclude,
    Run,
)
from job_runner.apps.job_runner.utils import correct_dst_difference


class JobTestCase(TestCase):
    """
    Tests for the job model.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs'
    ]

    def test_recursion(self):
        """
        Test that saving a resursive job-chain will raise a validation error.
        """
        job = Job.objects.get(pk=2)
        job.parent = Job.objects.get(pk=1)
        job.full_clean()
        job.save()

        job = Job.objects.get(pk=1)
        job.full_clean()
        job.parent = Job.objects.get(pk=2)
        self.assertRaises(ValidationError, job.full_clean)


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

    def test_reschedule(self):
        """
        Test reschedule.
        """
        self.assertEqual(1, Run.objects.filter(job_id=1).count())
        Job.objects.get(pk=1).reschedule()
        # because of the pre-scheduling, reschedule should result in max
        # 2 scheduled runs.
        self.assertEqual(2, Run.objects.filter(job_id=1).count())
        Job.objects.get(pk=1).reschedule()
        self.assertEqual(2, Run.objects.filter(job_id=1).count())

        Run.objects.filter(pk=1).update(
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            return_dts=timezone.now()
        )

        # we just completed one run, so reschedule should result in a new
        # schedule.
        Job.objects.get(pk=1).reschedule()
        self.assertEqual(3, Run.objects.filter(job_id=1).count())

        # make sure the last run is scheduled based on the schedule_dts of the
        # pre-last run
        runs = Run.objects.filter(job_id=1).all()
        self.assertEqual(
            correct_dst_difference(
                runs[1].schedule_dts,
                runs[1].schedule_dts + timedelta(days=1)
            ),
            runs[2].schedule_dts
        )

    def test_reschedule_not_in_past(self):
        """
        Test reschedule dts is never in the past.
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

        # we have to make sure to use correct_dst_difference since between
        # 31 days ago and tomorrow, we might have changed from or to DTS.
        self.assertEqual(
            run.schedule_dts,
            correct_dst_difference(
                dts_now - timedelta(days=31),
                dts_now + timedelta(days=1)
            )
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
            self.assertEqual(
                correct_dst_difference(in_dts, expected_dts),
                run.schedule_dts
            )

    def test_reschedule_with_exclude(self):
        """
        Test reschedule with exclude time.
        """
        job = Job.objects.get(pk=1)
        job.reschedule_interval_type = 'HOUR'
        job.save()

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            schedule_dts=timezone.make_aware(
                datetime(2032, 1, 1, 11, 59), timezone.get_default_timezone()),
            return_dts=timezone.make_aware(
                datetime(2032, 1, 1, 11, 59), timezone.get_default_timezone()),
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
        Test reschedule when there are already two runs scheduled.
        """
        job = Job.objects.get(pk=1)
        self.assertEqual(1, Run.objects.filter(job=job).count())

        Run.objects.filter(pk=1).update(
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            return_dts=timezone.now()
        )

        for x in range(2):
            Run.objects.create(
                job=job,
                schedule_dts=timezone.now()
            )

        self.assertEqual(3, Run.objects.filter(job=job).count())
        job.reschedule()
        self.assertEqual(3, Run.objects.filter(job=job).count())

    def test_reschedule_with_started_run(self):
        """
        Test reschedule when there is an other run started and one scheduled.
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
            schedule_dts=timezone.now()
        )

        Run.objects.create(
            job=job,
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
        )

        self.assertEqual(3, Run.objects.filter(job=job).count())
        job.reschedule()
        self.assertEqual(3, Run.objects.filter(job=job).count())

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

    def test_schedule_id_set_on_create(self):
        """
        Test that the ``schedule_id`` is set on create.
        """
        run = Run.objects.create(
            job=Job.objects.get(pk=1),
            schedule_dts=timezone.now()
        )
        self.assertTrue(run.pk == run.schedule_id)

    def test_mark_failed(self):
        """
        Test :meth:`.Run.mark_failed`.
        """
        run = Run.objects.get(pk=1)
        run.mark_failed('Test mark failed')

        run = Run.objects.get(pk=1)

        self.assertNotEqual(
            '',
            run.run_log.content
        )
        self.assertIsInstance(run.enqueue_dts, datetime)
        self.assertIsInstance(run.start_dts, datetime)
        self.assertIsInstance(run.return_dts, datetime)
        self.assertFalse(run.return_success)

    def test_mark_failed_on_completed_run(self):
        """
        Test :meth:`.Run.mark_failed` on completed run.

        In this case, :meth:`.Run.mark_failed` shouldn't do anything.

        """
        Run.objects.filter(pk=1).update(
            return_dts=timezone.now(),
            return_success=True,
        )
        run = Run.objects.get(pk=1)
        run.mark_failed('Test mark failed')
        run = Run.objects.get(pk=1)

        self.assertTrue(run.return_success)
