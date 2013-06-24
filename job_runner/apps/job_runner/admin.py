from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.utils import timezone
from django.utils.dateformat import DateFormat

from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    Project,
    RescheduleExclude,
    Run,
    Worker,
    WorkerPool,
)


class PermissionAdminMixin(object):
    """
    Mixin class to limit the number of visible items.
    """

    groups_path = None
    """
    A ``str`` containing the path to the groups.

    Example::

        'job_template__project__auth_groups'

    """

    fk_groups_path = {}
    """
    A ``dict`` containing the FK field name and as a value the corresponding
    model and path to the groups.

    Example::

        {
            'job_template': {
                'path': 'project__auth_groups',
                'model': JobTemplate,
            }
        }

    """

    def _filter_groups(self, request, qs, groups_path):
        if request.user.is_superuser:
            return qs

        if not request.user.groups.count():
            return qs.none()

        groups_or = None
        for group in request.user.groups.all():
            q_obj = Q(**{groups_path: group})
            if not groups_or:
                groups_or = q_obj
            else:
                groups_or = groups_or | q_obj

        return qs.filter(groups_or).distinct()

    def queryset(self, request):
        """
        Get results based on groups the user is in.

        If the user is a super-user, the user has access to everything. Else,
        the results are limited based on matching groups as set in the model.

        """
        qs = super(PermissionAdminMixin, self).queryset(request)
        return self._filter_groups(request, qs, self.groups_path)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in self.fk_groups_path:
            qs = self.fk_groups_path[db_field.name]['model'].objects.all()
            group_path = self.fk_groups_path[db_field.name]['path']
            kwargs['queryset'] = self._filter_groups(request, qs, group_path)

        return super(PermissionAdminMixin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)


class RunInlineAdmin(admin.TabularInline):
    """
    Inline admin for job runs.
    """
    model = Run
    fields = ['schedule_dts']
    max_num = 1

    def queryset(self, request):
        return self.model.objects.scheduled()


class RescheduleExcludeInlineAdmin(admin.TabularInline):
    """
    Inline admin for reschedule excludes.
    """
    model = RescheduleExclude


class ProjectAdmin(admin.ModelAdmin):
    """
    Admin interface for projects.
    """
    list_display = ('title', 'enqueue_is_enabled')
    list_filter = ('enqueue_is_enabled',)
    list_editable = ('enqueue_is_enabled',)
    filter_horizontal = ('groups', 'auth_groups', 'worker_pools',)
    save_as = True


class WorkerAdmin(admin.ModelAdmin):
    """
    Admin interface for workers.
    """
    list_display = (
        'title',
        'api_key',
        'enqueue_is_enabled',
        'ping_response',
        'worker_version',
        'concurrent_jobs',
    )
    list_filter = ('enqueue_is_enabled',)
    list_display_links = ('title',)
    list_editable = ('enqueue_is_enabled',)
    save_as = True

    def ping_response(self, obj):
        interval = settings.JOB_RUNNER_WORKER_PING_INTERVAL
        margin = settings.JOB_RUNNER_WORKER_PING_MARGIN

        if not obj.ping_response_dts:
            return '<span style="color: red;">(none)</span>'

        date_local = obj.ping_response_dts.astimezone(
            timezone.get_current_timezone())
        date_formatted = DateFormat(date_local)
        date_formatted = date_formatted.format(settings.DATETIME_FORMAT)

        if not obj.is_responsive():
            return (
                '<img src="{0}admin/img/icon_error.gif" /> '
                '<span style="color: red;">{1}</span>'.format(
                    settings.STATIC_URL,
                    date_formatted
                )
            )

        if (obj.ping_response_dts <
                timezone.now() - timedelta(seconds=interval + margin)):
            return (
                '<img src="{0}admin/img/icon_alert.gif" /> '
                '<span style="color: orange;">{1}</span>'.format(
                    settings.STATIC_URL,
                    date_formatted
                )
            )

        return (
            '<img src="{0}admin/img/icon_success.gif" /> '
            '<span style="color: green;">{1}</span>'.format(
                settings.STATIC_URL,
                date_formatted
            )
        )

    ping_response.allow_tags = True
    ping_response.short_description = 'Last ping response'


class WorkerPoolAdmin(admin.ModelAdmin):
    """
    Admin interface for worker-pools.
    """
    list_display = ('title', 'enqueue_is_enabled',)
    list_editable = ('enqueue_is_enabled',)
    filter_horizontal = ('workers',)
    save_as = True


class JobTemplateAdmin(PermissionAdminMixin, admin.ModelAdmin):
    """
    Admin interface for job-templates.
    """
    list_display = (
        'project', 'title', 'enqueue_is_enabled')
    list_filter = (
        'project', 'enqueue_is_enabled',)
    list_display_links = ('title',)
    list_editable = ('enqueue_is_enabled',)
    groups_path = 'project__auth_groups'
    fk_groups_path = {
        'project': {
            'model': Project,
            'path': 'auth_groups',
        }
    }
    save_as = True


class JobAdmin(PermissionAdminMixin, admin.ModelAdmin):
    """
    Admin interface for jobs.
    """
    list_display = (
        'job_template',
        'title',
        'worker_pool',
        'enqueue_is_enabled',
        'run_on_all_workers',
        'parent'
    )
    list_filter = (
        'enqueue_is_enabled',
        'run_on_all_workers',
        'schedule_children_on_error',
        'reschedule_interval_type',
        'job_template',
        'job_template__project',
        'worker_pool'
    )
    list_display_links = ('title',)
    list_editable = ('enqueue_is_enabled',)
    search_fields = ('title',)
    save_as = True
    inlines = [
        RunInlineAdmin,
        RescheduleExcludeInlineAdmin,
    ]
    groups_path = 'job_template__project__auth_groups'
    fk_groups_path = {
        'job_template': {
            'model': JobTemplate,
            'path': 'project__auth_groups',
        },
        'parent': {
            'model': Job,
            'path': 'job_template__project__auth_groups',
        }
    }

    fieldsets = (
        (None, {
            'fields': (
                'title',
                'job_template',
                'worker_pool',
                'run_on_all_workers',
                'schedule_children_on_error',
                'parent',
                'description',
            )
        }),
        ('Script', {
            'fields': ('script_content_partial',)
        }),
        ('Notifications', {
            'fields': ('notification_addresses',)
        }),
        ('Scheduling', {
            'fields': (
                'enqueue_is_enabled',
                'disable_enqueue_after_fails',
                'reschedule_interval',
                'reschedule_interval_type',
            ),
        }),
    )


admin.site.register(Job, JobAdmin)
admin.site.register(JobTemplate, JobTemplateAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Worker, WorkerAdmin)
admin.site.register(WorkerPool, WorkerPoolAdmin)
