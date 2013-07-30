from django.contrib.auth.models import Group
from tastypie import fields
from tastypie.authentication import MultiAuthentication, SessionAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource

from job_runner.apps.job_runner.auth import (
    HmacAuthentication, ModelAuthorization)
from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    KillRequest,
    Project,
    Run,
    RunLog,
    Worker,
    WorkerPool,
)


class NoRelatedSaveMixin(object):
    def save_related(self, *args, **kwargs):
        """
        Override to NOT save related models.

        In this case there is no need for it (it will update the related run
        every time a kill-requests is updated). Case where it goes wrong:

        * Kill requests has been executed -> PATCH kill_request
        * Run returned                    -> PATCH run

        Since the PATCH kill_request will do a select on the run (and getting
        the old data), around the same time the PATCH run will update the run
        and around the same time the PATCH kill_request will update the run
        as well, we will end-up with a not-updated run.

        An other option to work around this is to use the SERIALIZE transaction
        level. However, this seems not to be possible with all Django DB
        backends.

        See: https://github.com/toastdriven/django-tastypie/issues/742

        """
        pass


class GroupResource(ModelResource):
    """
    RESTful resource for Django groups.
    """
    class Meta:
        queryset = Group.objects.all()
        resource_name = 'group'
        allowed_methods = ['get']
        fields = ['name']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='project__worker_pools__workers__api_key',
            user_groups_path='',
        )


class ProjectResource(ModelResource):
    """
    RESTful resource for projects.
    """
    worker_pools = fields.ToManyField(
        'job_runner.apps.job_runner.api.WorkerPoolResource', 'worker_pools')

    auth_groups = fields.ToManyField(
        'job_runner.apps.job_runner.api.GroupResource', 'auth_groups')

    class Meta:
        queryset = Project.objects.all()
        resource_name = 'project'
        allowed_methods = ['get']
        fields = ['title', 'id', 'description', 'enqueue_is_enabled']
        filtering = {
            'id': 'exact',
            'title': 'exact',
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='worker_pools__workers__api_key',
            user_groups_path='groups',
        )


class WorkerPoolResource(ModelResource):
    """
    RESTful resource for worker-pools.
    """
    workers = fields.ToManyField(
        'job_runner.apps.job_runner.api.WorkerResource', 'workers')

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(WorkerPoolResource, self).build_filters(filters)

        if 'project_id' in filters:
            orm_filters.update({
                'project__id': filters['project_id']
            })

        return orm_filters

    class Meta:
        queryset = WorkerPool.objects.all()
        resource_name = 'worker_pool'
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        fields = [
            'id',
            'title',
            'description',
            'enqueue_is_enabled',
        ]
        filtering = {
            'title': 'exact',
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='workers__api_key',
            user_groups_path='project__groups',
        )


class WorkerResource(ModelResource):
    """
    RESTful resource for workers.
    """
    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(WorkerResource, self).build_filters(filters)

        if 'project_id' in filters:
            orm_filters.update({
                'workerpool__project__id': filters['project_id']
            })

        return orm_filters

    class Meta:
        queryset = Worker.objects.all()
        resource_name = 'worker'
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'patch']
        fields = [
            'id',
            'title',
            'api_key',
            'description',
            'enqueue_is_enabled',
            'ping_response_dts',
            'worker_version',
            'concurrent_jobs',
        ]
        filtering = {
            'api_key': ALL,
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='api_key',
            user_groups_path='workerpool__project__groups',
        )


class JobTemplateResource(ModelResource):
    """
    RESTful resource for job-templates.
    """
    project = fields.ToOneField(
        'job_runner.apps.job_runner.api.ProjectResource', 'project')

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(JobTemplateResource, self).build_filters(filters)

        if 'project_id' in filters:
            orm_filters.update({
                'project__id': filters['project_id']
            })

        return orm_filters

    class Meta:
        queryset = JobTemplate.objects.all()
        resource_name = 'job_template'
        allowed_methods = ['get']
        fields = ['id', 'title', 'description', 'enqueue_is_enabled']
        filtering = {
            'project': ALL_WITH_RELATIONS,
            'title': 'exact',
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='project__worker_pools__workers__api_key',
            user_groups_path='project__groups',
        )


class JobResource(NoRelatedSaveMixin, ModelResource):
    """
    RESTful resource for jobs.
    """
    job_template = fields.ToOneField(
        'job_runner.apps.job_runner.api.JobTemplateResource', 'job_template')
    worker_pool = fields.ToOneField(
        'job_runner.apps.job_runner.api.WorkerPoolResource', 'worker_pool')

    parent = fields.ToOneField('self', 'parent', null=True)
    children = fields.ToManyField('self', 'children', null=True)

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(JobResource, self).build_filters(filters)

        if 'project_id' in filters:
            orm_filters.update({
                'job_template__project__id': filters['project_id']
            })

        return orm_filters

    class Meta:
        queryset = Job.objects.all()
        resource_name = 'job'
        detail_allowed_methods = ['get', 'put', 'patch']
        list_allowed_methods = ['get', 'post']
        fields = [
            'id',
            'title',
            'description',
            'script_content',
            'script_content_partial',
            'enqueue_is_enabled',
            'reschedule_interval',
            'reschedule_interval_type',
            'run_on_all_workers',
            'schedule_children_on_error',
            'notification_addresses',
            'disable_enqueue_after_fails',
        ]
        filtering = {
            'job_template': ALL_WITH_RELATIONS,
            'title': 'exact',
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path=(
                'job_template__project__worker_pools__workers__api_key'),
            user_groups_path='job_template__project__groups',
            auth_user_groups_path='job_template__project__auth_groups',
        )


class RunResource(NoRelatedSaveMixin, ModelResource):
    """
    RESTful resource for job runs.
    """
    job = fields.ToOneField(
        'job_runner.apps.job_runner.api.JobResource', 'job')

    run_log = fields.ToOneField(
        'job_runner.apps.job_runner.api.RunLogResource', 'run_log',
        null=True,
        blank=True
    )

    worker = fields.ToOneField(
        'job_runner.apps.job_runner.api.WorkerResource',
        'worker',
        null=True,
        blank=True,
    )

    class Meta:
        queryset = Run.objects.filter()
        resource_name = 'run'
        detail_allowed_methods = ['get', 'patch']
        list_allowed_methods = ['get', 'post']
        filtering = {
            'schedule_dts': ALL,
            'is_manual': ALL,
            'job': ALL_WITH_RELATIONS,
            'worker': ALL_WITH_RELATIONS,
        }

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path=(
                'job__job_template__project__worker_pools__workers__api_key'),
            user_groups_path='job__job_template__project__groups',
            auth_user_groups_path='job__job_template__project__auth_groups',
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

        if 'state' in filters and filters['state'] == 'last_completed':
            jobs = Job.objects.all()
            last_completed_schedule_ids = [
                job.last_completed_schedule_id for job in jobs]

            state_filters['last_completed'] = {
                'enqueue_dts__isnull': False,
                'start_dts__isnull': False,
                'return_dts__isnull': False,
                'schedule_id__in': last_completed_schedule_ids
            }

        if 'state' in filters and filters['state'] in state_filters:
            orm_filters.update(state_filters[filters['state']])

        if 'project_id' in filters:
            orm_filters.update({
                'job__job_template__project__id': filters['project_id']
            })

        return orm_filters


class KillRequestResource(NoRelatedSaveMixin, ModelResource):
    """
    RESTful resource for kill requests.
    """
    run = fields.ToOneField(
        'job_runner.apps.job_runner.api.RunResource', 'run')

    class Meta:
        queryset = KillRequest.objects.all()
        resource_name = 'kill_request'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'patch']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='run__job__worker_pool__workers__api_key',
            user_groups_path='run__job__job_template__project__groups',
            auth_user_groups_path=(
                'run__job__job_template__project__auth_groups'),
        )


class RunLogResource(NoRelatedSaveMixin, ModelResource):
    """
    RESTful resource for run log-output.
    """
    run = fields.ToOneField(
        'job_runner.apps.job_runner.api.RunResource', 'run')

    class Meta:
        queryset = RunLog.objects.all()
        resource_name = 'run_log'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'patch']

        authentication = MultiAuthentication(
            SessionAuthentication(), HmacAuthentication())

        authorization = ModelAuthorization(
            api_key_path='run__job__worker_pool__workers__api_key',
            user_groups_path='run__job__job_template__project__groups',
            auth_user_groups_path=(
                'run__job__job_template__project__auth_groups'),
        )
