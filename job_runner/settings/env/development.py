import os

from job_runner.settings.base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '..', 'database.sqlite'),
    }
}

JOB_RUNNER_WS_SERVER = 'ws://localhost:5000/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
