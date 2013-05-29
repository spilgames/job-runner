from django.test import TestCase
from django.utils import timezone
from mock import Mock, call

from job_runner.apps.job_runner.management.commands.broadcast_queue import (
    Command)
from job_runner.apps.job_runner.models import (
    Job, JobTemplate, KillRequest, Project, Run, Worker, WorkerPool)


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

    def test__broadcast_kill_requests(self):
        """
        Test :meth:`.Command._broadcast_kill_requests`.
        """
        worker = Worker.objects.get(pk=1)
        run = Run.objects.get(pk=1)
        run.start_dts = timezone.now()
        run.pid = 1234
        run.worker = worker
        run.save()
        KillRequest.objects.create(
            run=run,
            schedule_dts=timezone.now()
        )

        command = Command()

        command.publisher = Mock()
        command._broadcast_kill_requests()

        self.assertEqual([
            call([
                'master.broadcast.worker1',
                '{"action": "kill", "kill_request_id": 1}'
            ])
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs(self):
        """
        Test :meth:`.Command._broadcast_runs`.
        """
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
            call([
                'master.broadcast.worker1',
                '{"action": "enqueue", "run_id": 1}'
            ]),
            call([
                'master.broadcast.worker2',
                '{"action": "enqueue", "run_id": 2}'
            ]),
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_run_on_all_workers(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``run_on_all_workers=True``.
        """
        job = Job.objects.get(pk=1)
        job.run_on_all_workers = True
        job.save()

        pool = WorkerPool.objects.get(pk=1)
        pool.workers.add(Worker.objects.get(pk=2))
        pool.save()

        Run.objects.get(pk=2).delete()

        command = Command()
        command.publisher = Mock()

        command._broadcast_runs()

        self.assertEqual([
            call([
                'master.broadcast.worker1',
                '{"action": "enqueue", "run_id": 3}'
            ]),
            call([
                'master.broadcast.worker2',
                '{"action": "enqueue", "run_id": 4}'
            ]),
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_project_disabled_enqueue(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``enqueue_is_enabled=False``
        for :class:`.Project`.
        """
        Project.objects.update(enqueue_is_enabled=False)
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_worker_disabled_enqueue(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``enqueue_is_enabled=False``
        for :class:`.Worker`.
        """
        Worker.objects.update(enqueue_is_enabled=False)
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_job_template_disabled_enqueue(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``enqueue_is_enabled=False``
        for :class:`.JobTemplate`.
        """
        JobTemplate.objects.update(enqueue_is_enabled=False)
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_disabled_enqueue(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``enqueue_is_enabled=False``
        for :class:`.Run`.
        """
        Job.objects.update(enqueue_is_enabled=False)
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_with_active_run(self):
        """
        Test :meth:`.Command._broadcast_runs` with still one active run.
        """
        Run.objects.create(
            job=Job.objects.get(pk=1),
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
        )
        Run.objects.create(
            job=Job.objects.get(pk=2),
            schedule_dts=timezone.now(),
            enqueue_dts=timezone.now(),
        )

        command = Command()
        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([], command.publisher.send_multipart.call_args_list)

    def test__broadcast_runs_disabled_enqueue_with_manual(self):
        """
        Test :meth:`.Command._broadcast_runs` with ``enqueue_is_enabled=False``
        but with manual one.
        """
        Job.objects.update(enqueue_is_enabled=False)
        Run.objects.filter(pk=2).update(is_manual=True)
        command = Command()

        command.publisher = Mock()
        command._broadcast_runs()

        self.assertEqual([
            call([
                'master.broadcast.worker2',
                '{"action": "enqueue", "run_id": 2}'
            ]),
        ], command.publisher.send_multipart.call_args_list)

    def test__broadcast_worker_ping(self):
        """
        Test :meth:`.Command._broadcast_worker_ping`.
        """
        command = Command()
        command.publisher = Mock()

        command._broadcast_worker_ping()

        self.assertEqual([
            call([
                'master.broadcast.worker1',
                '{"action": "ping"}'
            ]),
            call([
                'master.broadcast.worker2',
                '{"action": "ping"}'
            ]),
        ], command.publisher.send_multipart.call_args_list)
