import hashlib
import hmac
import json
from datetime import datetime

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    Project,
    Run,
    Worker,
)


class ApiTestBase(TestCase):
    """
    Base class for API testing.
    """
    def get(self, path, *args, **kwargs):
        api_key = hmac.new(
            'verysecret', 'GET{0}'.format(path), hashlib.sha1).hexdigest()

        return self.client.get(
            path,
            *args,
            ACCEPT='application/json',
            HTTP_AUTHORIZATION='ApiKey worker1:{0}'.format(api_key)
        )

    def get_json(self, path, *args, **kwargs):
        response = self.get(path, *args, **kwargs)
        return json.loads(response.content)

    def patch(self, path, data):
        json_data = json.dumps(data)
        api_key = hmac.new(
            'verysecret', 'PATCH{0}{1}'.format(path, json_data), hashlib.sha1
        ).hexdigest()

        return self.client.post(
            path,
            data=json_data,
            content_type='application/json',
            ACCEPT='application/json',
            HTTP_AUTHORIZATION='ApiKey worker1:{0}'.format(api_key),
            HTTP_X_HTTP_METHOD_OVERRIDE='PATCH',
        )


class ProjectTestCase(ApiTestBase):
    """
    Tests for the project interface.
    """
    fixtures = ['test_auth', 'test_project', 'test_worker']

    def test_project_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/project/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_projects_count(self):
        """
        Test that we have two projects in the database.
        """
        self.assertEqual(2, Project.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/project/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test project 1', json_data['objects'][0]['title'])

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/project/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test project 1', json_data['objects'][0]['title'])


class WorkerTestCase(ApiTestBase):
    """
    Tests for the worker interface.
    """
    fixtures = ['test_auth', 'test_project', 'test_worker']

    def test_worker_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/worker/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_worker_count(self):
        """
        Test worker count in the DB.
        """
        self.assertEqual(2, Worker.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/worker/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test worker 1', json_data['objects'][0]['title'])

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/worker/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test worker 1', json_data['objects'][0]['title'])


class JobTemplateTestCase(ApiTestBase):
    """
    Tests for the job-template interface.
    """
    fixtures = [
        'test_auth', 'test_project', 'test_worker', 'test_job_template']

    def test_job_template_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/job_template/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_job_template_count(self):
        """
        Test job-template count in the db.
        """
        self.assertEqual(2, JobTemplate.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/job_template/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test template 1', json_data['objects'][0]['title'])

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/job_template/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test template 1', json_data['objects'][0]['title'])


class JobTestCase(ApiTestBase):
    """
    Tests for the job interface.
    """
    fixtures = [
        'test_auth',
        'test_project',
        'test_worker',
        'test_job_template',
        'test_job',
    ]

    def test_job_methods(self):
        """
        Test allowed methods on jobs.
        """
        response = self.get('/api/v1/job/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(
            ['get', 'put'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_job_count(self):
        """
        Test the job count in the db.
        """
        self.assertEqual(2, Job.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/job/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test job 1', json_data['objects'][0]['title'])

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/job/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Test job 1', json_data['objects'][0]['title'])


class RunTestCase(ApiTestBase):
    """
    Tests for the run interface.
    """
    fixtures = [
        'test_auth',
        'test_project',
        'test_worker',
        'test_job_template',
        'test_job',
    ]

    def test_run_methods(self):
        """
        Test allowed methods on runs.
        """
        response = self.get('/api/v1/run/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual([
            'get',
            'patch',
        ], json_data['allowed_detail_http_methods'])
        self.assertEqual(
            ['get', 'post'], json_data['allowed_list_http_methods'])

    def test_run_count(self):
        """
        Test the run count in the db.
        """
        self.assertEqual(2, Run.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/run/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual(1, json_data['objects'][0]['id'])

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/run/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual(1, json_data['objects'][0]['id'])

    def test_scheduled(self):
        """
        Test listing scheduled runs.
        """
        expected = [
            ('scheduled', 1),
            ('in_queue', 0),
            ('started', 0),
            ('completed', 0),
            ('completed_successful', 0),
            ('completed_with_error', 0),
        ]

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_in_queue(self):
        """
        Test listing runs in queue.
        """
        expected = [
            ('scheduled', 0),
            ('in_queue', 1),
            ('started', 0),
            ('completed', 0),
            ('completed_successful', 0),
            ('completed_with_error', 0),
        ]

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.save()

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_started(self):
        """
        Test listing runs that are started.
        """
        expected = [
            ('scheduled', 0),
            ('in_queue', 0),
            ('started', 1),
            ('completed', 0),
            ('completed_successful', 0),
            ('completed_with_error', 0),
        ]

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.start_dts = timezone.now()
        run.save()

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_completed(self):
        """
        Test listing runs that are completed.
        """
        expected = [
            ('scheduled', 0),
            ('in_queue', 0),
            ('started', 0),
            ('completed', 1),
            ('completed_successful', 1),
            ('completed_with_error', 0),
        ]

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.start_dts = timezone.now()
        run.return_dts = timezone.now()
        run.return_success = True
        run.save()

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_completed_with_error(self):
        """
        Test listing runs that are completed with error.
        """
        expected = [
            ('scheduled', 0),
            ('in_queue', 0),
            ('started', 0),
            ('completed', 1),
            ('completed_successful', 0),
            ('completed_with_error', 1),
        ]

        run = Run.objects.get(pk=1)
        run.enqueue_dts = timezone.now()
        run.start_dts = timezone.now()
        run.return_dts = timezone.now()
        run.return_success = False
        run.save()

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_patch_run_1(self):
        """
        Test PATCH ``/api/v1/run/1/``.
        """
        enqueue_dts = timezone.now()

        response = self.patch(
            '/api/v1/run/1/',
            {
                'enqueue_dts': enqueue_dts.isoformat(' ')
            }
        )

        self.assertEqual(202, response.status_code)
        run = Run.objects.get(pk=1)
        self.assertEqual(enqueue_dts, run.enqueue_dts)

    def test_patch_with_reschedule(self):
        """
        Test PATCH ``/api/v1/run/1/`` causing a reschedule.
        """
        return_dts = timezone.now()
        Run.objects.update(enqueue_dts=timezone.now())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': return_dts.isoformat(' '),
                'return_success': True,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(2, Run.objects.filter(job_id=1).count())
        self.assertEqual(
            return_dts, Run.objects.filter(job_id=1)[0].return_dts)

    def test_returned_with_error(self):
        """
        Test PATCH ``/api/v1/run/1/`` returned with error.

        This is expected to send e-mail notifications out.

        """
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': False,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertTrue(hasattr(mail, 'outbox'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(4, len(mail.outbox[0].to))
        self.assertEqual('Run error for: Test job 1', mail.outbox[0].subject)

    def test_returned_with_error_disable_enqueue(self):
        """
        Test PATCH ``/api/v1/run/1/`` error disables enqueue.

        This is expected to disable the enqueue.

        """
        job = Job.objects.get(pk=1)
        job.disable_enqueue_after_fails = 3
        job.save()

        for i in range(3):
            response = self.patch(
                '/api/v1/run/1/',
                {
                    'return_dts': timezone.now().isoformat(' '),
                    'return_success': False,
                }
            )

            self.assertEqual(202, response.status_code)
            job = Job.objects.get(pk=1)
            self.assertTrue(job.enqueue_is_enabled)
            self.assertEqual(i + 1, job.fail_times)

        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': False,
            }
        )

        job = Job.objects.get(pk=1)
        self.assertFalse(job.enqueue_is_enabled)

    def test_create_new_run(self):
        """
        Test create a new run by performing a ``POST``.
        """
        self.client.login(username='admin', password='admin')

        response = self.client.post(
            '/api/v1/run/',
            data=json.dumps({
                'job': '/api/v1/job/1/',
                'schedule_dts': '2013-01-01 00:00:00',
            }),
            content_type='application/json',
            ACCEPT='application/json',
        )

        self.assertEqual(201, response.status_code)
        run = Run.objects.filter(job_id=1)[1]
        self.assertEqual(
            timezone.make_aware(
                datetime(2013, 1, 1),
                timezone.get_default_timezone()
            ),
            run.schedule_dts
        )

    def test_create_new_run_no_permission(self):
        """
        Test create a new run by performing a ``POST`` with invalid group.
        """
        template = JobTemplate.objects.get(pk=1)
        template.auth_groups = [Group.objects.get(pk=2)]
        template.save()

        self.client.login(username='admin', password='admin')

        response = self.client.post(
            '/api/v1/run/',
            data=json.dumps({
                'job': '/api/v1/job/1/',
                'schedule_dts': '2013-01-01 00:00:00',
            }),
            content_type='application/json',
            ACCEPT='application/json',
        )

        self.assertEqual(400, response.status_code)


class ChainedRunTestCase(ApiTestBase):
    """
    Tests for the run interface with chaining.
    """
    fixtures = [
        'test_auth',
        'test_project',
        'test_worker',
        'test_job_template',
        'test_job',
        'test_child_job',
    ]

    def test_patch_with_reschedule(self):
        """
        Test PATCH ``/api/v1/run/1/`` for chained job.

        """
        Run.objects.update(enqueue_dts=timezone.now())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': True,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(2, Job.objects.get(pk=1).run_set.count())
        self.assertEqual(1, Job.objects.get(pk=3).run_set.count())

    def test_patch_with_reschedule_no_children_reschedule(self):
        """
        Test PATCH ``/api/v1/run/1/`` for chained job but not reschedule
        children.

        """
        Run.objects.update(
            enqueue_dts=timezone.now(),
            schedule_children=False,
        )
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': True,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(2, Job.objects.get(pk=1).run_set.count())
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())
