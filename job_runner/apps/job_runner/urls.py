from django.conf.urls.defaults import patterns

from job_runner.apps.job_runner.views import DashboardView


urlpatterns = patterns('',
    (r'^$', DashboardView.as_view()),
)
