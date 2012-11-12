import hashlib
import hmac
import json
# from datetime import datetime

# from django.contrib.auth.models import Group
# from django.core import mail
from django.test import TestCase

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
            'key', 'PATCH{0}{1}'.format(path, json_data), hashlib.sha1
        ).hexdigest()

        return self.client.post(
            path,
            data=json_data,
            content_type='application/json',
            ACCEPT='application/json',
            HTTP_AUTHORIZATION='ApiKey test:{0}'.format(api_key),
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
        self.assertEqual(['get'], json_data['allowed_detail_http_methods'])
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

#     def test_get_runs(self):
#         """
#         Test GET ``/api/v1/run/``.
#         """
#         response = self.get('/api/v1/run/')
#         self.assertEqual(200, response.status_code)

#         json_data = json.loads(response.content)
#         self.assertEqual(1, len(json_data['objects']))
#         self.assertEqual(1, json_data['objects'][0]['id'])
#         self.assertEqual(
#             '/api/v1/job/1/', json_data['objects'][0]['job'])

#     def test_get_run_1(self):
#         """
#         Test GET ``/api/v1/run/1/``.
#         """
#         response = self.get('/api/v1/run/1/')
#         self.assertEqual(200, response.status_code)

#         json_data = json.loads(response.content)
#         self.assertEqual(1, json_data['id'])
#         self.assertEqual('/api/v1/job/1/', json_data['job'])

#     def test_scheduled(self):
#         """
#         Test listing scheduled runs.
#         """
#         expected = [
#             ('scheduled', 1),
#             ('in_queue', 0),
#             ('started', 0),
#             ('completed', 0),
#             ('completed_successful', 0),
#             ('completed_with_error', 0),
#         ]

#         for argument, expected in expected:
#             json_data = self.get_json(
#                 '/api/v1/run/?state={0}'.format(argument))
#             self.assertEqual(expected, len(json_data['objects']))

#     def test_in_queue(self):
#         """
#         Test listing runs in queue.
#         """
#         expected = [
#             ('scheduled', 0),
#             ('in_queue', 1),
#             ('started', 0),
#             ('completed', 0),
#             ('completed_successful', 0),
#             ('completed_with_error', 0),
#         ]

#         run = Run.objects.get(pk=1)
#         run.enqueue_dts = datetime.utcnow()
#         run.save()

#         for argument, expected in expected:
#             json_data = self.get_json(
#                 '/api/v1/run/?state={0}'.format(argument))
#             self.assertEqual(expected, len(json_data['objects']))

#     def test_started(self):
#         """
#         Test listing runs that are started.
#         """
#         expected = [
#             ('scheduled', 0),
#             ('in_queue', 0),
#             ('started', 1),
#             ('completed', 0),
#             ('completed_successful', 0),
#             ('completed_with_error', 0),
#         ]

#         run = Run.objects.get(pk=1)
#         run.enqueue_dts = datetime.utcnow()
#         run.start_dts = datetime.utcnow()
#         run.save()

#         for argument, expected in expected:
#             json_data = self.get_json(
#                 '/api/v1/run/?state={0}'.format(argument))
#             self.assertEqual(expected, len(json_data['objects']))

#     def test_completed(self):
#         """
#         Test listing runs that are completed.
#         """
#         expected = [
#             ('scheduled', 0),
#             ('in_queue', 0),
#             ('started', 0),
#             ('completed', 1),
#             ('completed_successful', 1),
#             ('completed_with_error', 0),
#         ]

#         run = Run.objects.get(pk=1)
#         run.enqueue_dts = datetime.utcnow()
#         run.start_dts = datetime.utcnow()
#         run.return_dts = datetime.utcnow()
#         run.return_success = True
#         run.save()

#         for argument, expected in expected:
#             json_data = self.get_json(
#                 '/api/v1/run/?state={0}'.format(argument))
#             self.assertEqual(expected, len(json_data['objects']))

#     def test_completed_with_error(self):
#         """
#         Test listing runs that are completed with error.
#         """
#         expected = [
#             ('scheduled', 0),
#             ('in_queue', 0),
#             ('started', 0),
#             ('completed', 1),
#             ('completed_successful', 0),
#             ('completed_with_error', 1),
#         ]

#         run = Run.objects.get(pk=1)
#         run.enqueue_dts = datetime.utcnow()
#         run.start_dts = datetime.utcnow()
#         run.return_dts = datetime.utcnow()
#         run.return_success = False
#         run.save()

#         for argument, expected in expected:
#             json_data = self.get_json(
#                 '/api/v1/run/?state={0}'.format(argument))
#             self.assertEqual(expected, len(json_data['objects']))

#     def test_patch_run_1(self):
#         """
#         Test PATCH ``/api/v1/run/1/``.
#         """
#         response = self.patch(
#             '/api/v1/run/1/',
#             {
#                 'enqueue_dts': datetime.utcnow().isoformat(' ')
#             }
#         )

#         self.assertEqual(202, response.status_code)

#     def test_patch_with_reschedule(self):
#         """
#         Test PATCH ``/api/v1/run/1/`` causing a reschedule.
#         """
#         response = self.patch(
#             '/api/v1/run/1/',
#             {
#                 'return_dts': datetime.utcnow().isoformat(' '),
#                 'return_success': True,
#             }
#         )

#         self.assertEqual(202, response.status_code)
#         self.assertEqual(2, Run.objects.count())

#     def test_returned_with_error(self):
#         """
#         Test PATCH ``/api/v1/run/1/`` returned with error.

#         This is expected to send e-mail notifications out.

#         .. note:: Make sure you test this with the following setting::

#             EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

#         """
#         response = self.patch(
#             '/api/v1/run/1/',
#             {
#                 'return_dts': datetime.utcnow().isoformat(' '),
#                 'return_success': False,
#             }
#         )

#         self.assertEqual(202, response.status_code)
#         self.assertTrue(hasattr(mail, 'outbox'))
#         self.assertEqual(1, len(mail.outbox))
#         self.assertEqual(6, len(mail.outbox[0].to))
#         self.assertEqual('Run error for: Test job', mail.outbox[0].subject)

#     def test_create_new_run(self):
#         """
#         Test create a new run by performing a ``POST``.
#         """
#         job = Job.objects.get(pk=1)
#         job.one_of_groups.add(Group.objects.get(pk=1))
#         job.save()

#         self.client.login(username='admin', password='admin')

#         response = self.client.post(
#             '/api/v1/run/',
#             data=json.dumps({
#                 'job': '/api/v1/job/1/',
#                 'schedule_dts': '2013-01-01 00:00:00',
#             }),
#             content_type='application/json',
#             ACCEPT='application/json',
#         )

#         self.assertEqual(201, response.status_code)

#     def test_create_new_run_no_permission(self):
#         """
#         Test create a new run by performing a ``POST`` with invalid group.
#         """
#         job = Job.objects.get(pk=1)
#         job.one_of_groups = [Group.objects.get(pk=2)]
#         job.save()

#         self.client.login(username='admin', password='admin')

#         response = self.client.post(
#             '/api/v1/run/',
#             data=json.dumps({
#                 'job': '/api/v1/job/1/',
#                 'schedule_dts': '2013-01-01 00:00:00',
#             }),
#             content_type='application/json',
#             ACCEPT='application/json',
#         )

#         self.assertEqual(400, response.status_code)


# class ChainedRunTestCase(ApiTestBase):
#     """
#     Tests for the run interface with chaining.
#     """
#     fixtures = [
#         'test_job', 'test_child_job', 'test_server', 'test_script_template']

#     def test_patch_with_reschedule(self):
#         """
#         Test PATCH ``/api/v1/run/1/`` for chained job.

#         """
#         response = self.patch(
#             '/api/v1/run/1/',
#             {
#                 'return_dts': datetime.utcnow().isoformat(' '),
#                 'return_success': True,
#             }
#         )

#         self.assertEqual(202, response.status_code)
#         self.assertEqual(2, Job.objects.get(pk=1).run_set.count())
#         self.assertEqual(1, Job.objects.get(pk=2).run_set.count())
