import os

from job_runner.settings.base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '..', 'test_database.sqlite'),
    }
}

TIME_ZONE = 'Europe/Amsterdam'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

JOB_RUNNER_WS_SERVER = 'ws://localhost:5000/'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Make sure that test with naive datetime objects will fail
import warnings
warnings.filterwarnings(
    'error',
    r"DateTimeField received a naive datetime",
    RuntimeWarning,
    r'django\.db\.models\.fields'
)
