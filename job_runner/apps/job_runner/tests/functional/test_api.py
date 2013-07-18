import hashlib
import hmac
import json
import urllib
from datetime import datetime

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from mock import Mock, patch

from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    KillRequest,
    Project,
    Run,
    RunLog,
    Worker,
    WorkerPool,
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

    def post(self, path, data, method_override='POST'):
        json_data = json.dumps(data)
        api_key = hmac.new(
            'verysecret', '{0}{1}{2}'.format(method_override, path, json_data),
            hashlib.sha1
        ).hexdigest()

        return self.client.post(
            path,
            data=json_data,
            content_type='application/json',
            ACCEPT='application/json',
            HTTP_AUTHORIZATION='ApiKey worker1:{0}'.format(api_key),
            HTTP_X_HTTP_METHOD_OVERRIDE=method_override,
        )

    def patch(self, path, data):
        return self.post(path, data, method_override='PATCH')


class GroupTestCase(ApiTestBase):
    """
    Tests for the group interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_project_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/group/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/group/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Group 1', json_data['objects'][0]['name'])

        response = self.get('/api/v1/group/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/group/2/')
        self.assertEqual(401, response.status_code)

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/group/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Group 1', json_data['objects'][0]['name'])

        response = self.client.get(
            '/api/v1/group/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/group/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

    def test_filter_on_title(self):
        """
        Test filtering on project title.
        """
        response = self.get('/api/v1/project/?{0}'.format(
            urllib.urlencode({'title': 'Test project 1'})))
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, json_data['objects'][0]['id'])


class ProjectTestCase(ApiTestBase):
    """
    Tests for the project interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

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

        response = self.get('/api/v1/project/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/project/2/')
        self.assertEqual(401, response.status_code)

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

        response = self.client.get(
            '/api/v1/project/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/project/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)


class WorkerPoolTestCase(ApiTestBase):
    """
    Tests for the worker-pool interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_worker_pool_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/worker_pool/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
        self.assertEqual(['get'], json_data['allowed_list_http_methods'])

    def test_worker_pool_count(self):
        """
        Test worker-pool count in the DB.
        """
        self.assertEqual(2, WorkerPool.objects.count())

    def test_api_authorization(self):
        """
        Test API authorization (API-key has access to one object).
        """
        response = self.get('/api/v1/worker_pool/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Pool 1', json_data['objects'][0]['title'])

        response = self.get('/api/v1/worker_pool/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/worker_pool/2/')
        self.assertEqual(401, response.status_code)

    def test_user_authorization(self):
        """
        Test user authorization (user has only access to one object).
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(
            '/api/v1/worker_pool/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, len(json_data['objects']))
        self.assertEqual('Pool 1', json_data['objects'][0]['title'])

        response = self.client.get(
            '/api/v1/worker_pool/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/worker_pool/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

    def test_filter_on_title(self):
        """
        Test filter on worker-pool title.
        """
        response = self.get('/api/v1/worker_pool/?{0}'.format(
            urllib.urlencode({'title': 'Pool 1'})))
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, json_data['objects'][0]['id'])


class WorkerTestCase(ApiTestBase):
    """
    Tests for the worker interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_worker_methods(self):
        """
        Test allowed methods.
        """
        response = self.get('/api/v1/worker/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(
            ['get', 'patch'], json_data['allowed_detail_http_methods'])
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

        response = self.get('/api/v1/worker/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/worker/2/')
        self.assertEqual(401, response.status_code)

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

        response = self.client.get(
            '/api/v1/worker/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/worker/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

    def test_patch_ping_response_dts(self):
        """
        Test PATCH the ping_response_dts field.
        """
        dts = timezone.now()
        response = self.patch(
            '/api/v1/worker/1/',
            {'ping_response_dts': dts.isoformat(' ')}
        )
        self.assertEqual(202, response.status_code)

        worker = Worker.objects.get(pk=1)
        self.assertEqual(dts, worker.ping_response_dts)

    def test_patch_ping_response_no_permissions(self):
        """
        Test PATCH the ping_response_dts without having permission.
        """
        dts = timezone.now()
        response = self.patch(
            '/api/v1/worker/2/',
            {'ping_response_dts': dts.isoformat(' ')}
        )
        self.assertEqual(401, response.status_code)


class JobTemplateTestCase(ApiTestBase):
    """
    Tests for the job-template interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

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

        response = self.get('/api/v1/job_template/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/job_template/2/')
        self.assertEqual(401, response.status_code)

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

        response = self.client.get(
            '/api/v1/job_template/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/job_template/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

    def test_filter_on_title(self):
        """
        Test filtering a job-template on title.
        """
        response = self.get('/api/v1/job_template/?{0}'.format(
            urllib.urlencode({'title': 'Test template 1'})))
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, json_data['objects'][0]['id'])


class JobTestCase(ApiTestBase):
    """
    Tests for the job interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_job_methods(self):
        """
        Test allowed methods on jobs.
        """
        response = self.get('/api/v1/job/schema/')
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertItemsEqual(
            ['get', 'put', 'patch'],
            json_data['allowed_detail_http_methods']
        )
        self.assertItemsEqual(
            ['get', 'post'],
            json_data['allowed_list_http_methods']
        )

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

        response = self.get('/api/v1/job/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/job/2/')
        self.assertEqual(401, response.status_code)

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

        response = self.client.get(
            '/api/v1/job/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/job/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

    def test_filter_on_title(self):
        """
        Test filtering on job-title.
        """
        response = self.get('/api/v1/job/?{0}'.format(urllib.urlencode({
            'title': 'Test job 1',
        })))
        self.assertEqual(200, response.status_code)

        json_data = json.loads(response.content)
        self.assertEqual(1, json_data['objects'][0]['id'])


class RunTestCase(ApiTestBase):
    """
    Tests for the run interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
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

        response = self.get('/api/v1/run/1/')
        self.assertEqual(200, response.status_code)

        response = self.get('/api/v1/run/2/')
        self.assertEqual(401, response.status_code)

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

        response = self.client.get(
            '/api/v1/run/1/', ACCEPT='application/json')
        self.assertEqual(200, response.status_code)

        response = self.client.get(
            '/api/v1/run/2/', ACCEPT='application/json')
        self.assertEqual(401, response.status_code)

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

    @patch('job_runner.apps.job_runner.signals.post_run_update', Mock())
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

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
            return_dts=timezone.now(),
            return_success=True,
        )

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

        Run.objects.filter(pk=1).update(
            enqueue_dts=timezone.now(),
            start_dts=timezone.now(),
            return_dts=timezone.now(),
            return_success=False
        )

        for argument, expected in expected:
            json_data = self.get_json(
                '/api/v1/run/?state={0}'.format(argument))
            self.assertEqual(expected, len(json_data['objects']))

    def test_patch_run(self):
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

    def test_patch_run_no_permission(self):
        """
        Test PATCH ``/api/v1/run/2/`` (we don't have access to this object).
        """
        enqueue_dts = timezone.now()

        response = self.patch(
            '/api/v1/run/2/',
            {
                'enqueue_dts': enqueue_dts.isoformat(' ')
            }
        )

        self.assertEqual(401, response.status_code)

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
        self.assertEqual(1, Job.objects.get(pk=1).last_completed_schedule_id)

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
        self.assertEqual(1, job.last_completed_schedule_id)

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
        project = Project.objects.get(pk=1)
        project.auth_groups = [Group.objects.get(pk=2)]
        project.save()

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

        self.assertEqual(401, response.status_code)


class ChainedRunTestCase(ApiTestBase):
    """
    Tests for the run interface with chaining.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
        'test_child_job',
    ]

    def test_patch_with_reschedule(self):
        """
        Test PATCH ``/api/v1/run/1/`` for chained job.

        """
        Run.objects.update(enqueue_dts=timezone.now())
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': True,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(1, Job.objects.get(pk=3).run_set.count())

    def test_patch_failed_run(self):
        """
        Test PATCH ``/api/v1/run/1/`` and mark run as failed.

        In this case, we're not expecting the job to schedule it's child.

        """
        Run.objects.update(enqueue_dts=timezone.now())
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': False,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())

    def test_patch_failed_run_with_schedule_child(self):
        """
        Test PATCH ``/api/v1/run/1/`` as failed, but schedule child.

        Since we've set ``schedule_children_on_error=True``, we expect that
        the chain will continue, even when the job failed.

        """
        Run.objects.update(enqueue_dts=timezone.now())
        Job.objects.filter(pk=1).update(schedule_children_on_error=True)
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': False,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(1, Job.objects.get(pk=3).run_set.count())

    def test_patch_with_disabled_child(self):
        """
        Test PATCH ``/api/v1/run/1/`` for chained job with disabled child.

        When enqueue_is_enabled=False, we do not expect that the child will
        be scheduled.

        """
        Job.objects.filter(pk=3).update(enqueue_is_enabled=False)
        Run.objects.update(enqueue_dts=timezone.now())
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())
        response = self.patch(
            '/api/v1/run/1/',
            {
                'return_dts': timezone.now().isoformat(' '),
                'return_success': True,
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())

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
        self.assertEqual(0, Job.objects.get(pk=3).run_set.count())


class KillRequestTestCase(ApiTestBase):
    """
    Tests for the kill request interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_post_new_kill_request(self):
        """
        Test POST ``/api/v1/kill_request/``.
        """
        response = self.post(
            '/api/v1/kill_request/',
            {
                'run': '/api/v1/run/1/',
            }
        )

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, KillRequest.objects.filter(run_id=1).count())

    def test_post_new_kill_request_no_permission(self):
        """
        Test POST ``/api/v1/kill_request/`` with run we don't have access to.
        """
        response = self.post(
            '/api/v1/kill_request/',
            {
                'run': '/api/v1/run/2/',
            }
        )
        self.assertEqual(401, response.status_code)


class RunLogTestCase(ApiTestBase):
    """
    Tests for the run log interface.
    """
    fixtures = [
        'test_auth',
        'test_projects',
        'test_workers',
        'test_worker_pools',
        'test_job_templates',
        'test_jobs',
    ]

    def test_post_new_run_log(self):
        """
        Test POST ``/api/v1/run_log/``.
        """
        response = self.post(
            '/api/v1/run_log/',
            {
                'run': '/api/v1/run/1/',
                'content': 'foo bar',
            }
        )
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, RunLog.objects.filter(run_id=1).count())

    def test_post_new_run_log_no_access(self):
        """
        Test POST ``/api/v1/run_log/`` with run we don't have access to.
        """
        response = self.post(
            '/api/v1/run_log/',
            {
                'run': '/api/v1/run/2/',
                'content': 'foo bar',
            }
        )
        self.assertEqual(401, response.status_code)

    def test_update_log(self):
        """
        Test update a log item.
        """
        response = self.post(
            '/api/v1/run_log/',
            {
                'run': '/api/v1/run/1/',
                'content': 'foo bar',
            }
        )
        self.assertEqual(201, response.status_code)

        response = self.patch(
            '/api/v1/run_log/1/',
            {
                'content': 'bar foo',
            }
        )
        self.assertEqual(202, response.status_code)
