from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from job_runner.apps.job_runner.views import DashboardView


view = login_required(DashboardView.as_view())


urlpatterns = patterns(
    '',
    url(
        r'^no-projects/$',
        view,
        name='no-projects',
    ),
    url(
        r'^project/(?P<project_id>\d+)/$',
        view,
        name='project'
    ),
    url(
        r'^project/(?P<project_id>\d+)/runs/$',
        view,
        name='runs'
    ),
    url(
        r'^project/(?P<project_id>\d+)/runs/(?P<run_id>\d+)/$',
        view,
        name='runs_run'
    ),
    url(
        r'^project/(?P<project_id>\d+)/jobs/$',
        view,
        name='jobs'
    ),
    url(
        r'^project/(?P<project_id>\d+)/jobs/(?P<job_id>\d+)/$',
        view,
        name='job'
    ),
    url(
        (
            r'^project/(?P<project_id>\d+)/jobs/'
            r'(?P<job_id>\d+)/runs/(?P<run_id>\d+)/$'
        ),
        view,
        name='job_run'
    ),
    url(
        r'^$',
        view,
        name='index'
    ),
)
