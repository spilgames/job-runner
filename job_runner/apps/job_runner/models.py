import calendar
from datetime import timedelta
import logging

from django.conf import settings
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

logger = logging.getLogger(__name__)


RESCHEDULE_INTERVAL_TYPE_CHOICES = (
    ('MINUTE', 'Every x minutes'),
    ('HOUR', 'Every x hours'),
    ('DAY', 'Every x days'),
    ('MONTH', 'Every x months'),
)


def validate_positive(value):
    """
    Validate that the value is positive (> 0).
    """
    if value <= 0:
        raise ValidationError(u'The input should be greater than 0.')


def validate_no_recursion(value, seen=[]):
    """
    Validate that there is no recursion in the job-chain.
    """
    # when the validate_no_recursion function is invoked, the ``value`` will
    # be the id of the object referencing to, so we have to lookup this object
    # first
    if isinstance(value, (int, long)):
        value = Job.objects.get(pk=value)

    if value in seen:
        raise ValidationError(u'Recursive loop of jobs detected.')
    seen.append(value)

    if value.parent:
        validate_no_recursion(value.parent, seen)

    return None


class RescheduleException(Exception):
    """
    Exception used when a rescheduling failed.
    """


class Project(models.Model):
    """
    Projects
    """
    title = models.CharField(max_length=255, db_index=True)
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

    # the worker will send back the worker version and concurrent jobs on
    # ping response
    worker_version = models.CharField(
        max_length=100, blank=True, null=True, editable=False)
    concurrent_jobs = models.PositiveIntegerField(
        blank=True, null=True, editable=False)

    def __unicode__(self):
        return self.title

    def log_name(self):
        return u'"{0}"({1})'.format(self.title, self.pk)

    def is_responsive(self):
        """
        Return ``bool`` indicating if the worker is resposive.
        """
        unresponsive_intervals = \
            settings.JOB_RUNNER_WORKER_UNRESPONSIVE_AFTER_INTERVALS
        ping_interval = settings.JOB_RUNNER_WORKER_PING_INTERVAL
        ping_margin = settings.JOB_RUNNER_WORKER_PING_MARGIN

        acceptable_delta = timedelta(
            seconds=(unresponsive_intervals * ping_interval) + ping_margin)

        if self.ping_response_dts:
            if self.ping_response_dts + acceptable_delta >= timezone.now():
                return True

        logger.error('Worker {0} is not responsive'.format(self.log_name()))
        return False

    class Meta:
        ordering = ('title', )


class WorkerPool(models.Model):
    """
    Worker-pool.
    """
    title = models.CharField(max_length=255, db_index=True)
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

    def log_name(self):
        return u'"{0}"({1})'.format(self.title, self.pk)

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
    title = models.CharField(max_length=255, db_index=True)
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
        'self',
        blank=True,
        null=True,
        related_name='children',
        validators=[validate_no_recursion],
    )
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
        help_text=(
            'Run this job on all workers within the selected pool. '
            'NOTE: be aware that the job will be duplicated to run in '
            'parallel on all workers of the pool. Leave this box unticked to '
            'have the job run once on only one of the workers.'
        )
    )
    schedule_children_on_error = models.BooleanField(
        default=False,
        help_text=(
            'Schedule children even when the job fails (or fails on one of '
            'the workers in case you ticked run on all workers). '
            'Normally a failed job means that it will stop the chain.'
        )
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(
        blank=True,
        help_text='You can use Markdown syntax to format this description.',
    )
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

    def log_name(self):
        return u'"{0}"({1})'.format(self.title, self.pk)

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

        """
        if not dts:
            dts = timezone.now()

        logger.info('Scheduling {0} on {1}'.format(self.log_name(), dts))

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
        active_runs = self.run_set.filter(return_dts__isnull=True)
        active_schedule_ids = []

        # TODO: is there a way in the Django ORM to achieve the same?
        for active_run in active_runs:
            if not active_run.schedule_id in active_schedule_ids:
                active_schedule_ids.append(active_run.schedule_id)

        # since we are pre-scheduling (a new run is created, before the
        # scheduled run is sent to the worker), having one schedule id is valid
        if len(active_schedule_ids) > 1:
            logger.error('Multiple ({0}) active schedule ids for {1}'.format(
                active_schedule_ids, self.log_name()))
            return

        logger.info('Attempting rescheduling {0}'.format(self.log_name()))

        # check if job is setup for re-scheduling
        if self.reschedule_interval_type and self.reschedule_interval:
            try:
                # order by -pk to get the last non-manual scheduled run
                # from which we need to increment
                last_run = self.run_set.filter(
                    is_manual=False).order_by('-pk')[0]
            except IndexError:
                logger.error('Reschedule failed for {0}: IndexError'.format(
                    self.log_name()))
                return

            try:
                reschedule_date = self._get_reschedule_date(
                    last_run.schedule_dts)

                # correct daylight saving-time changes to make sure we keep
                # re-scheduling at the same hour (in local time).
                reschedule_date = correct_dst_difference(
                    last_run.schedule_dts, reschedule_date)

                self.schedule(reschedule_date)
                logger.info('Rescheduled {0} for {1}'.format(
                    self.log_name(), reschedule_date))
            except RescheduleException:
                logger.error(
                    'Reschedule failed for {0}: RescheduleException'.format(
                        self.log_name()))
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

    def log_name(self):
        return u'Id: {0} ({1})'.format(self.pk, self.job.log_name())

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

    def mark_failed(self, message):
        """
        Mark this run as failed (if ``return_dts`` is not set yet).

        :param message:
            A ``str`` explaining why this run was marked as failed.

        """
        if self.return_dts:
            return

        if not self.enqueue_dts:
            self.enqueue_dts = timezone.now()

        if not self.start_dts:
            self.start_dts = timezone.now()

        self.return_dts = timezone.now()
        self.return_success = False

        log_message = 'This run for {0} was marked as failed. \
            Reason: {1}'.format(
            self.log_name(), message)
        logger.error(log_message)

        try:
            # In rare cases, it is possible that there is already a log for
            # the run.
            run_log = self.run_log
            run_log.content = log_message
            run_log.save()
        except RunLog.DoesNotExist:
            RunLog.objects.create(
                run=self,
                content=log_message
            )

        # saving the records triggers the sending of error e-mails so we need
        # to save the log before saving the run record.
        self.save()


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
