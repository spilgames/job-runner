from django.test import TestCase

from mock import Mock, patch

from job_runner.apps.job_runner.auth import validate_hmac


class ModuleTestCase(TestCase):
    """
    Tests for :mod:`apps.job_runner.auth`.
    """
    @patch('job_runner.apps.job_runner.auth.Worker')
    def test_validate_hmac_valid_api_key(self, Worker):
        """
        Test :func:`.validate_hmac` with valid API key.
        """
        request = Mock()
        request.method = 'POST'
        request.META = {
            'HTTP_AUTHORIZATION': (
                'ApiKey api_user:9bfd7ed2a963182c4005c851f5f862cc97607f7b'),
        }
        request.get_full_path.return_value = 'full_request_path'
        request.raw_post_data = 'raw_post_data'

        api_user = Worker.objects.get.return_value
        api_user.secret = 'foobar'

        self.assertTrue(validate_hmac(request))

    @patch('job_runner.apps.job_runner.auth.Worker')
    def test_validate_hmac_invalid_api_key(self, Worker):
        """
        Test :func:`.validate_hmac` with invalid API key.
        """
        request = Mock()
        request.method = 'GET'
        request.META = {
            'HTTP_AUTHORIZATION': (
                'ApiKey api_user:9bfd7ed2a963182c4005c851f5f862cc97607f7b'),
        }
        request.get_full_path.return_value = 'full_request_path'
        request.raw_post_data = 'raw_post_data'

        api_user = Worker.objects.get.return_value
        api_user.secret = 'foobar'

        self.assertFalse(validate_hmac(request))
