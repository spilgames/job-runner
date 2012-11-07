from django.conf import settings
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = 'job_runner/index.html'

    def get_context_data(self, **kwargs):
        context_data = super(DashboardView, self).get_context_data(**kwargs)
        context_data['ws_server'] = settings.JOB_RUNNER_WS_SERVER
        return context_data
