import copy
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.db import models
from django.template import Context, Template
from django.template.loader import get_template
from django.utils import timezone

from job_runner.apps.job_runner.managers import RunManager


RESCHEDULE_INTERVAL_TYPE_CHOICES = (
    ('MINUTE', 'Every x minutes'),
    ('HOUR', 'Every x hours'),
    ('DAY', 'Every x days'),
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
    groups = models.ManyToManyField(Group)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )

    def __unicode__(self):
        return self.title

    def get_notification_addresses(self):
        """
        Return a ``list`` notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        return [x.strip() for x in addresses]


class Worker(models.Model):
    """
    Workers
    """
    title = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, db_index=True, unique=True)
    secret = models.CharField(max_length=255, db_index=True)
    project = models.ForeignKey(Project)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )

    def __unicode__(self):
        return self.title

    def get_notification_addresses(self):
        """
        Return a ``list`` of notification addresses.
        """
        addresses = self.notification_addresses.strip().split('\n')
        addresses = [x.strip() for x in addresses]
        addresses.extend(self.project.get_notification_addresses())
        return addresses


class JobTemplate(models.Model):
    """
    Job templates
    """
    title = models.CharField(max_length=255)
    body = models.TextField(help_text=(
        'Use {{ content|safe }} at the place where you want to render the '
        'script content of the job'
    ))
    worker = models.ForeignKey(Worker)
    auth_groups = models.ManyToManyField(Group, blank=True)
    notification_addresses = models.TextField(
        help_text='Separate e-mail addresses by a newline',
        blank=True,
    )

    def __unicode__(self):
        return self.title

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
        addresses = [x.strip() for x in addresses]
        addresses.extend(self.worker.get_notification_addresses())
        return addresses


class Job(models.Model):
    """
    Contains the job data.
    """
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')
    job_template = models.ForeignKey(JobTemplate)
    title = models.CharField(max_length=255)
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
    )
    reschedule_type = models.CharField(
        max_length=18,
        blank=True,
        choices=RESCHEDULE_TYPE_CHOICES,
    )
    notification_addresses = models.TextField(
        help_text='Separate addresses by a newline',
        blank=True,
    )

    class Meta:
        ordering = ('title', )
        unique_together = (('title', 'job_template'),)

    def __unicode__(self):
        return self.title

    def reschedule(self):
        """
        Reschedule job.

        This will check if the job is setup for reschedule. Then it will
        try to get the next reschedule date. When getting this date fails
        (eg: when the rescheduling always falls within the reschedule exclude),
        it will send out an e-mail to the Job-Runner admins and the e-mail
        addresses that are setup for this job, script and server.

        """
        if self.run_set.awaiting_enqueue().count():
            return

        if (self.reschedule_type and self.reschedule_interval_type
                and self.reschedule_interval):
            last_run = self.run_set.filter(is_manual=False)[0]

            if last_run.return_dts:
                if self.reschedule_type == 'AFTER_SCHEDULE_DTS':
                    reference_date = last_run.schedule_dts
                elif self.reschedule_type == 'AFTER_COMPLETE_DTS':
                    reference_date = last_run.return_dts

                if self.reschedule_interval_type == 'MINUTE':
                    delta = timedelta(minutes=self.reschedule_interval)
                elif self.reschedule_interval_type == 'HOUR':
                    delta = timedelta(hours=self.reschedule_interval)
                elif self.reschedule_interval_type == 'DAY':
                    delta = timedelta(days=self.reschedule_interval)

                try:
                    reschedule_date = self._get_reschedule_date(
                        reference_date, delta)

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
        addresses = [x.strip() for x in addresses]
        addresses.extend(self.job_template.get_notification_addresses())
        return addresses

    def _get_reschedule_date(
            self, reference_date, reschedule_delta, increment_date=None):
        """
        Return a reschedule datetime.

        This will take the reschedule exclude times into account when
        generating a new date/time.

        :param reference_date:
            The reference :class:`datetime.datetime` to generate the
            reschedule date from.

        :param reschedule_delta:
            The :class:`datetime.timedelta` to increment the
            ``reference_date`` with.

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

        while (reference_date + reschedule_delta) < timezone.now():
            reference_date = reference_date + reschedule_delta

        if not increment_date:
            increment_date = reference_date

        elif (increment_date - reference_date) > timedelta(days=1):
            raise RescheduleException(
                'Unable to reschedule due to reschedule excludes')

        reschedule_date = increment_date + reschedule_delta

        for exclude in self.rescheduleexclude_set.all():
            if (reschedule_date.time() >= exclude.start_time
                and reschedule_date.time() <= exclude.end_time):
                return self._get_reschedule_date(
                    reference_date, reschedule_delta, reschedule_date)

        return reschedule_date


class RescheduleExclude(models.Model):
    """
    Exclude rules for rescheduling.
    """
    job = models.ForeignKey(Job)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __unicode__(self):
        return u'{0} - {1}'.format(self.start_time, self.end_time)


class Run(models.Model):
    """
    Contains the data related to a (scheduled) job run.
    """
    job = models.ForeignKey(Job)
    schedule_dts = models.DateTimeField(db_index=True)
    enqueue_dts = models.DateTimeField(null=True)
    start_dts = models.DateTimeField(null=True, db_index=True)
    return_dts = models.DateTimeField(null=True)
    return_success = models.NullBooleanField(
        default=None, null=True)
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
