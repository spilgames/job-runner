

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
            instance.send_error_notification()
            job.fail_times += 1

            # disable job when it failed more than x times
            if (job.disable_enqueue_after_fails and
                    job.fail_times > job.disable_enqueue_after_fails):
                job.enqueue_is_enabled = False

            job.save()

        job.reschedule()

        if instance.return_success:
            # reset the fail count
            job.fail_times = 0
            job.save()

        if instance.return_success and instance.schedule_children:
            # the job completed successfully and has children to schedule now
            for child in instance.job.children.all():
                child.schedule_now()
