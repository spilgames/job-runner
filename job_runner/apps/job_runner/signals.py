from job_runner.apps.job_runner import notifications


def post_run_create(sender, instance, raw, **kwargs):
    """
    Post action after creating a run instance.

    This will make sure the ``schedule_id`` field is set.

    """
    if not instance.schedule_id:
        instance.schedule_id = instance.id
        instance.save()


def post_run_update(sender, instance, created, raw, **kwargs):
    """
    Post action after saving a run instance.

    This will:

        * send an error notification by e-mail when the job failed
        * disable the job when it failed more times than allowed
        * schedule it's children (if applicable)

    """
    if created or raw:
        return

    job = instance.job

    if instance.return_dts:
        if instance.return_success is False:
            # the run failed
            notifications.run_failed(instance)
            job.fail_times += 1
            job.last_completed_schedule_id = instance.schedule_id

            # disable job when it failed more than x times
            if (job.disable_enqueue_after_fails and
                    job.fail_times > job.disable_enqueue_after_fails):
                job.enqueue_is_enabled = False

            job.save()

        else:
            # reset the fail count
            job.fail_times = 0
            job.last_completed_schedule_id = instance.schedule_id
            job.save()

        # on purpose we are not using .count() since with that, the
        # .select_for_update() does not have any effect.

        # we need to lock the selected records here, to make sure we do not
        # run this part in parallel (with the risk that when both transactions
        # are marking the run as finished, they still see each other as
        # unfinished since the transaction hasn't been committed yet).
        unfinished_siblings = len(instance.get_siblings().filter(
            return_dts__isnull=True).select_for_update())

        if instance.schedule_children and not unfinished_siblings:
            failed_siblings = instance.get_siblings().filter(
                return_success=False)

            if ((instance.return_success and not failed_siblings.count())
                    or job.schedule_children_on_error):
                for child in instance.job.children.all():
                    if child.enqueue_is_enabled:
                        child.schedule()
