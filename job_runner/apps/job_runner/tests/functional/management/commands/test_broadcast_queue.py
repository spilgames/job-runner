from django.test import TestCase
from mock import Mock, call

from job_runner.apps.job_runner.management.commands.broadcast_queue import (
    Command)

class CommandTestCase(TestCase):
    """
    Tests for :class:`.Command`.
    """
    fixtures = [
        'test_auth',
        'test_project',
        'test_worker',
        'test_job_template',
        'test_job',
    ]

    def test__broadcast(self):
        """
        Test :meth:`.Command._broadcast`.
        """
        command = Command()

        publisher = Mock()
        command._broadcast(publisher)

        self.assertEqual([
            call([
                'master.broadcast.worker2',
                '{"action": "enqueue", "run_id": 2}'
            ]),
            call([
                'master.broadcast.worker1',
                '{"action": "enqueue", "run_id": 1}'
            ]),
        ], publisher.send_multipart.call_args_list)
