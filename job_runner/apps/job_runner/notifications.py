import copy

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import get_template


def reschedule_failed(job):
    """
    Send out a notification that the given ``job`` failed to reschedule.
    """
    t = get_template('job_runner/email/reschedule_failed.txt')
    c = Context({
        'job': job,
        'hostname': settings.HOSTNAME,
    })
    email_body = t.render(c)

    addresses = copy.copy(settings.JOB_RUNNER_ADMIN_EMAILS)
    addresses.extend(job.get_notification_addresses())

    if addresses:
        send_mail(
            'Reschedule error for: {0}'.format(job.title),
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            addresses
        )
