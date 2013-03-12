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
        Return a QS filtered on runs's that are ready to enqueue.
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

            # when job enqueue is disabled
            Q(
                job__enqueue_is_enabled=False,
                is_manual=False
            ) |

            # when job-template enqueue is disabled
            Q(
                job__job_template__enqueue_is_enabled=False,
                is_manual=False
            ) |

            # when project enqueue is disabled
            Q(
                job__job_template__project__enqueue_is_enabled=False,
                is_manual=False
            ) |

            # when worker-pool enqueue is disabled
            Q(
                job__worker_pool__enqueue_is_enabled=False,
                is_manual=False
            ) |

            # exclude jobs that are still active
            Q(job__in=active_jobs)
        )


class KillRequestManager(models.Manager):
    """
    Custom manager for the KillRequest model.
    """
    def killable(self):
        """
        Return a QS filtered on requests that are killable.
        """
        qs = self.get_query_set()

        return qs.filter(
            # this should be always the case
            schedule_dts__lte=timezone.now(),

            # make sure it hasn't been executed already
            enqueue_dts__isnull=True,
            execute_dts__isnull=True,

            # make sure a pid is assigned to the run
            run__pid__isnull=False,

            # make sure the run is active
            run__start_dts__isnull=False,

            # make sure the run hasn't returned already
            run__return_dts__isnull=True,

            # make sure the run is assigned to a worker
            run__worker__isnull=False,
        )
