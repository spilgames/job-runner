from tastypie import fields
from tastypie.authentication import MultiAuthentication, SessionAuthentication
from tastypie.resources import ModelResource

from job_runner.apps.job_runner.auth import (
    HmacAuthentication, ModelAuthorization)
from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    Project,
    Run,
    Worker,
)


class ProjectResource(ModelResource):
    """
    RESTful resource for projects.
    """
    class Meta:
        queryset = Project.objects.all()
        resource_name = 'project'
        allowed_methods = ['get']
        fields = ['title', 'id']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='worker__api_key',
            user_groups_path='groups',
        )


class WorkerResource(ModelResource):
    """
    RESTful resource for workers.
    """
    project = fields.ToOneField(
        'job_runner.apps.job_runner.api.ProjectResource', 'project')

    class Meta:
        queryset = Worker.objects.all()
        resource_name = 'worker'
        allowed_methods = ['get']
        fields = ['title', 'api_key']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='api_key',
            user_groups_path='project__groups',
        )


class JobTemplateResource(ModelResource):
    """
    RESTful resource for job-templates.
    """
    worker = fields.ToOneField(
        'job_runner.apps.job_runner.api.WorkerResource', 'worker')

    class Meta:
        queryset = JobTemplate.objects.all()
        resource_name = 'job_template'
        allowed_methods = ['get']
        fields = ['title']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='worker__api_key',
            user_groups_path='worker__project__groups',
        )


class JobResource(ModelResource):
    """
    RESTful resource for jobs.
    """
    job_template = fields.ToOneField(
        'job_runner.apps.job_runner.api.JobTemplateResource', 'job_template')
    parent = fields.ToOneField('self', 'parent', null=True)
    children = fields.ToManyField('self', 'children', null=True)

    class Meta:
        queryset = Job.objects.all()
        resource_name = 'job'
        allowed_methods = ['get']
        fields = ['title', 'script_content']
        # filtering = {
        #     'server': ALL,
        # }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='job_template__worker__api_key',
            user_groups_path='job_template__worker__project__groups',
            auth_user_groups_path='job_template__auth_groups',
        )


class RunResource(ModelResource):
    """
    RESTful resource for job runs.
    """
    job = fields.ToOneField(
        'job_runner.apps.job_runner.api.JobResource', 'job')

    class Meta:
        queryset = Run.objects.all()
        resource_name = 'run'
        detail_allowed_methods = ['get', 'patch']
        list_allowed_methods = ['get', 'post']
        # filtering = {
        #     'schedule_dts': ALL,
        #     'job': ALL,
        # }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='job__job_template__worker__api_key',
            user_groups_path='job__job_template__worker__project__groups',
            auth_user_groups_path='job__job_template__auth_groups',
        )

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(RunResource, self).build_filters(filters)

        state_filters = {
            'scheduled': {
                'enqueue_dts__isnull': True,
            },
            'in_queue': {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': True,
            },
            'started': {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': False,
                'return_dts__isnull': True,
            },
            'completed': {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': False,
                'return_dts__isnull': False,
            },
            'completed_successful': {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': False,
                'return_dts__isnull': False,
                'return_success': True,
            },
            'completed_with_error': {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': False,
                'return_dts__isnull': False,
                'return_success': False,
            }
        }

        if 'state' in filters and filters['state'] in state_filters:
            orm_filters.update(state_filters[filters['state']])

        return orm_filters

    def obj_update(self, bundle, request=None, *args, **kwargs):
        """
        Override of the default obj_update method.

        This will call the ``reschedule`` method after a successful object
        update, which will re-schedule the job if needed.

        If the object update represents the returning of a run with error,
        it will call also ``send_error_notification`` method.

        """
        deserialized = self.deserialize(
            request,
            request.raw_post_data,
            format=request.META.get('CONTENT_TYPE', 'application/json')
        )

        result = super(RunResource, self).obj_update(
            bundle, request, *args, **kwargs)

        bundle.obj.job.reschedule()

        if (deserialized.get('return_dts', None)
            and deserialized.get('return_success', None) == False):
                bundle.obj.send_error_notification()
        elif (deserialized.get('return_dts', None)
            and deserialized.get('return_success', None) == True):
                for child in bundle.obj.job.children.all():
                    child.schedule_now()

        return result


# from tastypie import fields
# from tastypie.authentication import MultiAuthentication, SessionAuthentication
# from tastypie.constants import ALL
# from tastypie.resources import ModelResource

# from job_runner.apps.job_runner.auth import (
#     HmacAuthentication, RunAuthorization, JobAuthorization)
# from job_runner.apps.job_runner.models import Job, Run, Server


        # authorization = JobAuthorization()
