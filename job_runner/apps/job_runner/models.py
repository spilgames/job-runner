import calendar
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.template import Context, Template
from django.utils import timezone
from smart_selects.db_fields import ChainedForeignKey

from job_runner.apps.job_runner import notifications
from job_runner.apps.job_runner.managers import KillRequestManager, RunManager
from job_runner.apps.job_runner.signals import post_run_update, post_run_create
from job_runner.apps.job_runner.utils import correct_dst_difference


RESCHEDULE_INTERVAL_TYPE_CHOICES = (
    ('MINUTE', 'Every x minutes'),
    ('HOUR', 'Every x hours'),
    ('DAY', 'Every x days'),
    ('MONTH', 'Every x months'),
)

RESCHEDULE_TYPE_CHOICES = (
    ('AFTER_SCHEDULE_DTS', 'Increment schedule dts by interval'),
    ('AFTER_COMPLETE_DTS', 'Increment complete dts by interval'),
)


def validate_positive(value):
    """
    Validate that the value is positive (> 0).
    """
    if value <= 0:
        raise ValidationError(u'The input should be greater than 0.')


class RescheduleException(Exception):
    """
    Exception used when a rescheduling failed.
    """


class Project(models.Model):
    """
    Projects
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name='Viewers (groups)',
        help_text=(
            'These are the groups that can see the project in the dashboard. '
        )
    )
    auth_groups = models.ManyToManyField(
        Group,
        verbose_name='Project admins (groups)',
        blank=True,
        related_name='auth_groups_set',
        help_text=(
            'These are the groups that are authorized to see this project '
            'and its jobs in the admin and are able to re-schedule the jobs '
            'of this project in the dashboard.'
        )
    )
    worker_pools = models.ManyToManyField(
        'job_runner.WorkerPool',
        help_text=(
            'These are the worker-pools that will be available for this '
            'project.'
        )
    )
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, nothing for this project will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )

    def __unicode__(self):
        return self.title

    def get_notification_addresses(self):
        """
        Return a ``list`` notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        return [x.strip() for x in addresses if x.strip() != '']

    class Meta:
        ordering = ('title', )


class Worker(models.Model):
    """
    Workers
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    api_key = models.CharField(max_length=255, db_index=True, unique=True)
    secret = models.CharField(max_length=255, db_index=True)
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, nothing for this worker will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )
    ping_response_dts = models.DateTimeField(
        blank=True, null=True, editable=False)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title', )


class WorkerPool(models.Model):
    """
    Worker-pool.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, nothing for this worker-pool will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )
    workers = models.ManyToManyField(Worker)

    def __unicode__(self):
        return self.title

    def get_notification_addresses(self):
        """
        Return a ``list`` notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        return [x.strip() for x in addresses if x.strip() != '']

    class Meta:
        ordering = ('title', )


class JobTemplate(models.Model):
    """
    Job templates
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    body = models.TextField(help_text=(
        'Use {{ content|safe }} at the place where you want to render the '
        'script content of the job'
    ))
    project = models.ForeignKey(Project)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, nothing for this template will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )

    def __unicode__(self):
        return u'{0} > {1}'.format(self.project, self.title)

    def save(self, *args, **kwargs):
        """
        Override default save to re-save jobs.

        This will make sure that when the template changed, the cached version
        will be updated on the job level.

        """
        super(JobTemplate, self).save(*args, **kwargs)
        for job in self.job_set.all():
            job.save()

    def get_notification_addresses(self):
        """
        Return a ``list`` of notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        addresses = [x.strip() for x in addresses if x.strip() != '']
        addresses.extend(self.project.get_notification_addresses())
        return addresses

    class Meta:
        ordering = ('project__title', 'title', )


class Job(models.Model):
    """
    Contains the job data.
    """
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')
    job_template = models.ForeignKey(JobTemplate)
    worker_pool = ChainedForeignKey(
        WorkerPool,
        chained_field='job_template',
        chained_model_field='project__jobtemplate',
        show_all=False,
        auto_choose=False,
        help_text='Select a job-template first to see the available pools.',
    )
    run_on_all_workers = models.BooleanField(
        default=False,
        help_text='Run this job on all workers within the selected pool.',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    script_content_partial = models.TextField('script content')
    script_content = models.TextField(editable=False)
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, the job will not be added to the worker queue. '
            'This will not affect already running jobs.'
        )
    )
    reschedule_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_positive],
        help_text=(
            'A positive number (greater than 0). '
            'Leave blank if you do not want to re-schedule this job.'
        )
    )
    reschedule_interval_type = models.CharField(
        max_length=6,
        blank=True,
        choices=RESCHEDULE_INTERVAL_TYPE_CHOICES,
        db_index=True,
        help_text=(
            'Note: with montly re-scheduling, the date will be incremented '
            'by the number of days in the month.'
        )
    )
    reschedule_type = models.CharField(
        max_length=18,
        blank=True,
        choices=RESCHEDULE_TYPE_CHOICES,
        db_index=True,
    )
    notification_addresses = models.TextField(
        help_text='Separate addresses by a newline',
        blank=True,
    )
    fail_times = models.PositiveIntegerField(
        editable=False,
        default=0,
        help_text='The number of times this job failed in a row.',
    )
    disable_enqueue_after_fails = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=(
            'The number of times after which the enqueue-ing of a job should '
            'be disabled when it failed (blank = never disable enqeueue).'
        )
    )
    last_completed_schedule_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        editable=False,
    )

    class Meta:
        ordering = (
            'job_template__project__title',
            'job_template__title',
            'title',
        )
        unique_together = (('title', 'job_template'),)

    def __unicode__(self):
        return u'{0} > {1}'.format(self.job_template, self.title)

    def save(self, *args, **kwargs):
        t = Template(self.job_template.body)
        c = Context({'content': self.script_content_partial})
        self.script_content = t.render(c)
        super(Job, self).save(*args, **kwargs)

    def get_notification_addresses(self):
        """
        Return a ``list`` of notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        addresses = [x.strip() for x in addresses if x.strip() != '']
        addresses.extend(self.job_template.get_notification_addresses())
        addresses.extend(self.worker_pool.get_notification_addresses())
        return addresses

    def schedule(self, dts=None):
        """
        Schedule the job to run at the given ``dts``.

        :param dts:
            An instance of :class:`datetime.datetime` or ``None`` to schedule
            now.

        When the job is already scheduled to run now, but the run has not yet
        been picked up by the worker (the worker could be dead or the job
        enqueue is disabled), it will not schedule a new run.

        """
        if not dts:
            dts = timezone.now()

        # don't schedule a new run when it is already scheduled to run now
        runs = Run.objects.filter(
            job=self,
            schedule_dts__lte=timezone.now(),
            return_dts__isnull=True,
            is_manual=False,
        )
        if not runs.count():
            Run.objects.create(
                job=self,
                schedule_dts=dts,
            )

    def reschedule(self):
        """
        Reschedule job.

        This will check if the job is setup for reschedule. Then it will
        try to get the next reschedule date. When getting this date fails
        (eg: when the rescheduling always falls within the reschedule exclude),
        it will send out an e-mail to the Job-Runner admins and the e-mail
        addresses that are setup for this job, script and server.

        """
        # there is already an other run which is not finished yet, do
        # not re-schedule, it will be rescheduled when the other job
        # finishes
        if self.run_set.filter(return_dts__isnull=True).count():
            return

        # check if job is setup for re-scheduling
        if (self.reschedule_type and self.reschedule_interval_type
                and self.reschedule_interval):
            last_run = self.run_set.filter(is_manual=False)[0]

            if not last_run.return_dts:
                # we can't reschedule if there wasn't a previous run
                return

            # find the reschedule reference date
            if self.reschedule_type == 'AFTER_SCHEDULE_DTS':
                reference_date = last_run.schedule_dts
            elif self.reschedule_type == 'AFTER_COMPLETE_DTS':
                reference_date = last_run.return_dts

            try:
                reschedule_date = self._get_reschedule_date(reference_date)

                if self.reschedule_type == 'AFTER_SCHEDULE_DTS':
                    # correct daylight saving-time changes to make sure we keep
                    # re-scheduling at the same hour (in local time).
                    reschedule_date = correct_dst_difference(
                        last_run.schedule_dts, reschedule_date)

                self.schedule(reschedule_date)
            except RescheduleException:
                notifications.reschedule_failed(self)

    def _get_reschedule_incremented_dts(self, increment_date):
        """
        Increment the given ``reference_date`` with the reschedule interval.

        :param increment_date:
            An instance of :class:`!datetime.datetime` to increment.

        :return:
            An instance of :class:`!datetime.datetime`.

        """
        if self.reschedule_interval_type == 'MINUTE':
            return increment_date + timedelta(minutes=self.reschedule_interval)
        elif self.reschedule_interval_type == 'HOUR':
            return increment_date + timedelta(hours=self.reschedule_interval)
        elif self.reschedule_interval_type == 'DAY':
            return increment_date + timedelta(days=self.reschedule_interval)
        elif self.reschedule_interval_type == 'MONTH':
            # increment the dts with the number of days that are in the
            # ``reschedule_date``.
            reschedule_date = increment_date
            for x in range(self.reschedule_interval):
                days_in_month = calendar.monthrange(
                    reschedule_date.year, reschedule_date.month)
                reschedule_date = reschedule_date + timedelta(
                    days=days_in_month[1])
            return reschedule_date

    def _get_reschedule_date(
            self,
            reference_date,
            increment_date=None):
        """
        Return a reschedule datetime.

        This will take the reschedule exclude times into account when
        generating a new date/time.

        :param reference_date:
            The reference :class:`datetime.datetime` to generate the
            reschedule date from.

        :param increment_date:
            The :class:`datetime.datetime` to increment for calculating the
            reschedule date. This is optional and when not set, the
            ``reference_date`` will be used.

        :raises:
            :exc:`.RescheduleException` when the reschedule date can not
            be calculated. This is for example the case when a reschedule
            exclude exists which covers the whole day.

        :return:
            An instance of :class:`datetime.datetime`.

        """
        # make sure the reference_date is in the current tz, because we are
        # going to compare hours / minutes!
        reference_date = reference_date.astimezone(
            timezone.get_default_timezone())

        if not increment_date:
            increment_date = reference_date

        reschedule_date = self._get_reschedule_incremented_dts(increment_date)

        while reschedule_date < timezone.now():
            reschedule_date = self._get_reschedule_incremented_dts(
                reschedule_date)

        if (increment_date - reference_date) > timedelta(days=1):
            raise RescheduleException(
                'Unable to reschedule due to reschedule excludes')

        for exclude in self.rescheduleexclude_set.all():
            if (reschedule_date.time() >= exclude.start_time and
                    reschedule_date.time() <= exclude.end_time):
                return self._get_reschedule_date(
                    reference_date, reschedule_date)

        return reschedule_date


class RescheduleExclude(models.Model):
    """
    Exclude rules for rescheduling.
    """
    job = models.ForeignKey(Job)
    start_time = models.TimeField()
    end_time = models.TimeField()
    note = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return u'{0} - {1}'.format(self.start_time, self.end_time)


class Run(models.Model):
    """
    Contains the data related to a (scheduled) job run.
    """
    job = models.ForeignKey(Job)
    schedule_id = models.PositiveIntegerField(
        null=True, default=None, db_index=True)
    worker = models.ForeignKey(Worker, null=True, blank=True)
    schedule_dts = models.DateTimeField(db_index=True)
    enqueue_dts = models.DateTimeField(null=True, db_index=True)
    start_dts = models.DateTimeField(null=True, db_index=True)
    return_dts = models.DateTimeField(null=True, db_index=True)
    return_success = models.NullBooleanField(
        default=None, null=True, db_index=True)
    pid = models.PositiveIntegerField(null=True, default=None)
    is_manual = models.BooleanField(
        default=False, editable=False, db_index=True)
    schedule_children = models.BooleanField(
        default=True, editable=False, db_index=True)

    objects = RunManager()

    class Meta:
        ordering = (
            '-return_dts', '-start_dts', '-enqueue_dts', 'schedule_dts')

    @models.permalink
    def get_absolute_url(self):
        return ('job_runner:job_run', (), {
            'project_id': self.job.job_template.project.pk,
            'job_id': self.job.pk,
            'run_id': self.pk,
        })

    def get_siblings(self):
        """
        Return a ``QuerySet`` instance for the siblings of this run.
        """
        return self.__class__.objects.exclude(
            pk=self.pk,
            schedule_id__isnull=True,
        ).filter(
            schedule_id=self.schedule_id,
            job=self.job,
        )

    def get_schedule_id(self):
        if self.schedule_id:
            return self.schedule_id
        return self.pk


class KillRequest(models.Model):
    """
    Contains requests to kill active runs.
    """
    run = models.ForeignKey(Run)
    schedule_dts = models.DateTimeField(auto_now_add=True, db_index=True)
    enqueue_dts = models.DateTimeField(null=True, db_index=True)
    execute_dts = models.DateTimeField(null=True, db_index=True)

    objects = KillRequestManager()


class RunLog(models.Model):
    """
    Contains log output for runs.
    """
    run = models.OneToOneField(Run, related_name='run_log')
    content = models.TextField(null=True, default=None)

    class Meta:
        ordering = ('-run',)


signals.post_save.connect(post_run_update, sender=Run)
signals.post_save.connect(post_run_create, sender=Run)
