from django.db import models


class RunManager(models.Manager):
    """
    Custom manager for the Run model.
    """
    def awaiting_enqueue(self):
        """
        Return a QS filtered on run's that aren't enqueued yet.
        """
        qs = self.get_query_set()
        return qs.filter(enqueue_dts__isnull=True)
