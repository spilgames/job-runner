import os


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'static', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static', 'job_runner'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
     'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '&amp;nghghm8)r1*_s$)p^+p==513yu9*aphzdt*qlc-jr(eyrd!u_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'job_runner.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'job_runner.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    # has to be before admin app
    'grappelli',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'south',
    'tastypie',
    'compressor',
    'smart_selects',

    'job_runner.apps.job_runner',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


LOGIN_REDIRECT_URL = '/'

GRAPPELLI_ADMIN_HEADLINE = 'Job-Runner'
GRAPPELLI_ADMIN_TITLE = 'Job-Runner'


API_LIMIT_PER_PAGE = 200


JOB_RUNNER_WS_SERVER = 'ws://localhost:5000/'
"""
The URL to the Job-Runner WebSocket server.

This should be in the following format::

    ws://hostname:port/

"""


JOB_RUNNER_ADMIN_EMAILS = []
"""
A list of e-mail addresses of the Job-Runner admin(s).

This list will currently be used when a job failed to reschedule.

"""


JOB_RUNNER_BROADCASTER_PORT = 5556
"""
The port to which the queue broadcaster is binding to.

Unless there is a specific need, you can keep the default.

"""


JOB_RUNNER_WS_SERVER_HOSTNAME = 'localhost'
"""
The hostname of the WebSocket Server.
"""


JOB_RUNNER_WS_SERVER_PORT = 5555
"""
The port of the WebSocket Server.
"""


JOB_RUNNER_WORKER_PING_INTERVAL = 60 * 5
"""
The interval in seconds for sending ping-requests to the workers.
"""


JOB_RUNNER_WORKER_HEALTH_CHECK_INTERVAL = 60 * 5
"""
The interval in seconds for running the health check.
"""


JOB_RUNNER_WORKER_PING_MARGIN = 15
"""
The time to add to the interval before considering a worker is not responding.

This is needed since the ping / pong are async (the PING is sent over ZMQ, the
pong is done by making a request to the REST API).

"""


JOB_RUNNER_WORKER_UNRESPONSIVE_AFTER_INTERVALS = 3
"""
The number of missed ping responses after which to declare a worker
unresponsive.
"""


HOSTNAME = ''
"""
The hostname of the server.

This value is used for generating URL's in the notification e-mails.

"""
