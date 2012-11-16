from django.contrib import admin
from django.db.models import Q

from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    Project,
    RescheduleExclude,
    Run,
    Worker,
)


class PermissionAdminMixin(object):
    """
    Mixin class to limit the number of items displayed.
    """

    groups_path = None
    """
    A ``str`` containing the path to the groups.

    Example::

        'job_template__auth_groups'

    """

    fk_groups_path = {}
    """
    A ``dict`` containing the FK field name and as a value the corresponding
    model and path to the groups.

    Example::

        {
            'job_template': {
                'path': 'auth_groups',
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

        return qs.filter(groups_or)

    def queryset(self, request):
        """
        Get results based on groups the user is in.

        If the user is a super-user, the user has access to everything. Else,
        the results are limited based on matching groups as set in the model.

        """
        qs = super(PermissionAdminMixin, self).queryset(request)
        return self._filter_groups(request, qs, self.groups_path)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in self.fK_groups_path:
            qs = self.fK_groups_path[db_field.name]['model'].objects.all()
            group_path = self.fK_groups_path[db_field.name]['path']
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
        return self.model.objects.awaiting_enqueue()


class RescheduleExcludeInlineAdmin(admin.TabularInline):
    """
    Inline admin for reschedule excludes.
    """
    model = RescheduleExclude


class JobAdmin(PermissionAdminMixin, admin.ModelAdmin):
    """
    Admin interface for jobs.
    """
    list_display = ('title', 'job_template', 'reschedule_type', 'parent')
    inlines = [
        RunInlineAdmin,
        RescheduleExcludeInlineAdmin,
    ]
    groups_path = 'job_template__auth_groups'
    fK_groups_path = {
        'job_template': {
            'model': JobTemplate,
            'path': 'auth_groups',
        },
        'parent': {
            'model': Job,
            'path': 'job_template__auth_groups',
        }
    }

    fieldsets = (
        (None, {
            'fields': ('title', 'job_template', 'parent',)
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
                'reschedule_interval',
                'reschedule_interval_type',
                'reschedule_type',)
        }),
    )


admin.site.register(Job, JobAdmin)
admin.site.register(JobTemplate)
admin.site.register(Project)
admin.site.register(Worker)
