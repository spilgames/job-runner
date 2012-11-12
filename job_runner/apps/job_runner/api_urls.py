from django.conf.urls.defaults import include, patterns
from tastypie.api import Api

# from job_runner.apps.job_runner.api import (
#     JobResource, RunResource, ServerResource)


v1_api = Api(api_name='v1')
# v1_api.register(JobResource())
# v1_api.register(RunResource())
# v1_api.register(ServerResource())


urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
