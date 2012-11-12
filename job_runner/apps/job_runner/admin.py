from django.contrib import admin

from job_runner.apps.job_runner.models import (
    Job,
    JobTemplate,
    Project,
    RescheduleExclude,
    Run,
    Worker,
)


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


class JobAdmin(admin.ModelAdmin):
    """
    Admin interface for jobs.
    """
    list_display = ('title', 'job_template', 'reschedule_type', 'parent')
    inlines = [
        RunInlineAdmin,
        RescheduleExcludeInlineAdmin,
    ]

    fieldsets = (
        (None, {
            'fields': ('title', 'job_template',)
        }),
        ('Script', {
            'fields': ('script_content_partial',)
        }),
        ('Notifications', {
            'fields': ('notification_addresses',)
        }),
        ('Scheduling', {
            'fields': (
                'reschedule_interval',
                'reschedule_interval_type',
                'reschedule_type',)
        }),
    )


admin.site.register(Job, JobAdmin)
admin.site.register(JobTemplate)
admin.site.register(Project)
admin.site.register(Worker)
