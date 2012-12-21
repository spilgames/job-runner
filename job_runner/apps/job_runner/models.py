import calendar
import copy
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.db import models
from django.template import Context, Template
from django.template.loader import get_template
from django.utils import timezone

from job_runner.apps.job_runner.managers import KillRequestManager, RunManager


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
        help_text=(
            'These are the groups that can see the project in the dashboard. '
            'The admin permissions are set on template level. '

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
    project = models.ForeignKey(Project)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )
    enqueue_is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            'If unchecked, nothing for this worker will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )

    def __unicode__(self):
        return u'{0} - {1}'.format(self.title, self.project)

    def get_notification_addresses(self):
        """
        Return a ``list`` of notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        addresses = [x.strip() for x in addresses if x.strip() != '']
        addresses.extend(self.project.get_notification_addresses())
        return addresses

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
    worker = models.ForeignKey(Worker)
    auth_groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text=(
            'These are the groups that are authorized to see this template '
            'and its jobs in the admin and are able to re-schedule the jobs '
            'using this template in the dashboard.'
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
            'If unchecked, nothing for this template will be added to '
            'the worker queue. This will not affect already running jobs.'
        )
    )

    def __unicode__(self):
        return u'{0} - {1}'.format(self.title, self.worker)

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
        addresses.extend(self.worker.get_notification_addresses())
        return addresses

    class Meta:
        ordering = ('title', )


class Job(models.Model):
    """
    Contains the job data.
    """
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')
    job_template = models.ForeignKey(JobTemplate)
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
        help_text=('Leave blank if you do not want to re-schedule this job.')
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

    class Meta:
        ordering = ('title', )
        unique_together = (('title', 'job_template'),)

    def __unicode__(self):
        return u'{0} - {1}'.format(self.title, self.job_template)

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

        if (self.reschedule_type and self.reschedule_interval_type
                and self.reschedule_interval):
            last_run = self.run_set.filter(is_manual=False)[0]

            if last_run.return_dts:
                if self.reschedule_type == 'AFTER_SCHEDULE_DTS':
                    reference_date = last_run.schedule_dts
                elif self.reschedule_type == 'AFTER_COMPLETE_DTS':
                    reference_date = last_run.return_dts

                try:
                    reschedule_date = self._get_reschedule_date(reference_date)

                    Run.objects.create(
                        job=self,
                        schedule_dts=reschedule_date,
                    )

                except RescheduleException:
                    t = get_template('job_runner/email/reschedule_failed.txt')
                    c = Context({
                        'job': self,
                        'hostname': settings.HOSTNAME,
                    })
                    email_body = t.render(c)

                    addresses = copy.copy(settings.JOB_RUNNER_ADMIN_EMAILS)
                    addresses.extend(self.get_notification_addresses())

                    if addresses:
                        send_mail(
                            'Reschedule error for: {0}'.format(self.title),
                            email_body,
                            settings.DEFAULT_FROM_EMAIL,
                            addresses
                        )

    def schedule_now(self):
        """
        Schedule the job to run now.
        """
        Run.objects.create(
            job=self,
            schedule_dts=timezone.now(),
        )

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
        return addresses

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
    schedule_dts = models.DateTimeField(db_index=True)
    enqueue_dts = models.DateTimeField(null=True, db_index=True)
    start_dts = models.DateTimeField(null=True, db_index=True)
    return_dts = models.DateTimeField(null=True, db_index=True)
    return_success = models.NullBooleanField(
        default=None, null=True, db_index=True)
    pid = models.PositiveIntegerField(null=True, default=None)
    return_log = models.TextField(null=True, default=None)
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
            'project_id': self.job.job_template.worker.project.pk,
            'job_id': self.job.pk,
            'run_id': self.pk,
        })

    def send_error_notification(self):
        """
        Send out an error notification e-mail.
        """
        t = get_template('job_runner/email/job_failed.txt')
        c = Context({
            'time_zone': settings.TIME_ZONE,
            'run': self,
            'hostname': settings.HOSTNAME,
        })
        email_body = t.render(c)

        addresses = copy.copy(settings.JOB_RUNNER_ADMIN_EMAILS)
        addresses.extend(self.job.get_notification_addresses())

        if addresses:
            send_mail(
                'Run error for: {0}'.format(self.job.title),
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                addresses
            )


class KillRequest(models.Model):
    """
    Contains requests to kill active runs.
    """
    run = models.ForeignKey(Run)
    schedule_dts = models.DateTimeField(auto_now_add=True, db_index=True)
    enqueue_dts = models.DateTimeField(null=True, db_index=True)
    execute_dts = models.DateTimeField(null=True, db_index=True)

    objects = KillRequestManager()
