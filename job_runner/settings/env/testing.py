import os

from job_runner.settings.base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '..', 'test_database.sqlite'),
    }
}

TIME_ZONE = 'Europe/Amsterdam'

JOB_RUNNER_WS_SERVER = 'ws://localhost:5000/'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

JOB_RUNNER_WORKER_PING_INTERVAL = 60 * 5

JOB_RUNNER_WORKER_PING_MARGIN = 15

JOB_RUNNER_WORKER_MARK_JOB_FAILED_AFTER_INTERVALS = 3


# Make sure that test with naive datetime objects will fail
import warnings
warnings.filterwarnings(
    'error',
    r"DateTimeField received a naive datetime",
    RuntimeWarning,
    r'django\.db\.models\.fields'
)
