from job_runner.apps.job_runner import notifications


def post_run_update(sender, instance, created, raw, **kwargs):
    """
    Post action after saving a run instance.

    This will call the ``reschedule`` method after a successful object
    update, which will re-schedule the job if needed (incl. children).

    If the object update represents the returning of a run with error,
    it will call also ``send_error_notification`` method.

    """
    if created or raw:
        return

    job = instance.job

    if instance.return_dts:
        if instance.return_success is False:
            # the run failed
            notifications.run_failed(instance)
            job.fail_times += 1

            # disable job when it failed more than x times
            if (job.disable_enqueue_after_fails and
                    job.fail_times > job.disable_enqueue_after_fails):
                job.enqueue_is_enabled = False

            job.save()

        unfinished_siblings = instance.get_siblings().filter(
            return_dts__isnull=True)

        if not unfinished_siblings.count():
            job.reschedule()

        if instance.return_success:
            # reset the fail count
            job.fail_times = 0
            job.save()

        if (instance.return_success and instance.schedule_children
                and not unfinished_siblings.count()):

            failed_siblings = instance.get_siblings().filter(
                return_success=False)

            if not failed_siblings.count():
                # the job completed successfully including it's siblings
                # and has children to schedule now
                for child in instance.job.children.all():
                    child.schedule()
