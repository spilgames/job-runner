from datetime import datetime, timedelta

from django.test import TestCase
from django.utils.timezone import get_current_timezone

from job_runner.apps.job_runner.utils import correct_dst_difference


class ModuleTestCase(TestCase):
    """
    Tests for :mod:`~job_runner.apps.job_runner.utils`.
    """
    def test_correct_dts_difference(self):
        """
        Test :func:`.correct_dst_difference`.

        This will test that during a DST change (from +1 to +2), the
        :func:`.correct_dst_difference` function will make sure that the
        local will stay the same.

        """
        tzinfo = get_current_timezone()
        prev_dts = tzinfo.localize(datetime(2013, 3, 30, 4))
        next_dts = prev_dts + timedelta(days=1)
        expected_next_dts = tzinfo.localize(datetime(2013, 3, 31, 4))

        # test that indeed there is a DST change
        self.assertEqual(timedelta(hours=1), prev_dts.utcoffset())
        self.assertEqual(timedelta(hours=2), expected_next_dts.utcoffset())

        # test that normally, the job would be scheduled at 05:00
        self.assertEqual(
            tzinfo.localize(datetime(2013, 3, 31, 5)),
            next_dts
        )

        # test that correct_dst_difference is correcting this to 04:00
        self.assertEqual(
            expected_next_dts,
            correct_dst_difference(prev_dts, next_dts)
        )
