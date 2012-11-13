from django.conf.urls.defaults import patterns
from django.contrib.auth.decorators import login_required

from job_runner.apps.job_runner.views import DashboardView


urlpatterns = patterns('',
    (r'^(|project/.*)$', login_required(DashboardView.as_view())),
)
