from django.db import models
from django.db.models import Q
from django.utils import timezone


class RunManager(models.Manager):
    """
    Custom manager for the Run model.
    """
    def scheduled(self):
        """
        Return a QS filtered on run's are in the scheduled state.
        """
        qs = self.get_query_set()
        return qs.filter(enqueue_dts__isnull=True)

    def enqueueable(self):
        """
        Return a QS filterd on runs's that are ready to enqueue.
        """
        job_qs = self.model.job.get_query_set()

        active_jobs = job_qs.filter(
            run__enqueue_dts__isnull=False,
            run__return_dts__isnull=True,
        )
        scheduled = self.scheduled()

        return scheduled.filter(
            # make sure it should be running now
            schedule_dts__lte=timezone.now(),
        ).exclude(
            # exclude auto scheduled jobs when enqueue is disabled
            Q(job__enqueue_is_enabled=False, is_manual=False) |

            # exclude jobs that are still active
            Q(job__in=active_jobs)
        )
