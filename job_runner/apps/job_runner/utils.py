from django.utils.timezone import get_current_timezone


def correct_dst_difference(previous_schedule_dts, next_schedule_dts):
    """
    Calculate the daylight saving-time difference between from and to DTS.

    Example: You are in Europe/Amsterdam timezone with DST (GMT+2) and you have
    a daily job running at 10:00 each morning. This translates to 08:00 UTC
    time. When switching to winter time (GMT+1), this would mean that the
    job suddenly starts at 09:00 (08:00 UTC + 1).

    By calculating the UTC offset between the previous schedule DTS and the
    next schedule DTS, we can find out if there is a DST change, and compensate
    this difference, to make sure the job will be re-scheduled at the same
    time in the local timezone.

    """
    previous_dts = previous_schedule_dts.astimezone(get_current_timezone())
    next_dts = next_schedule_dts.astimezone(get_current_timezone())

    dts_difference = previous_dts.utcoffset() - next_dts.utcoffset()

    return next_dts + dts_difference
