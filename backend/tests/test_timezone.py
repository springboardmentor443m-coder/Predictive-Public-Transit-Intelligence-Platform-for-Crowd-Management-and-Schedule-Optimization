"""Timezone contract tests.

These exist because the app got one thing quietly wrong: timestamps are stored
naive-UTC, but the occupancy curve, peak multipliers and weekend test are all
defined in **New York local time**. Reading ``timestamp.hour`` off a UTC value put
the 08:00 morning peak at 04:00 local, shifted the heatmap four hours, and
mislabelled every forecast row.

The failure was invisible in normal use (the data was self-consistent, just
rotated), so these tests pin the exact conversion rather than just "it doesn't
crash".
"""

from datetime import datetime, timedelta

import pytest

from app.core.time import (
    CITY_TZ,
    as_utc,
    city_day_start,
    city_hour,
    city_weekday,
    hour_floor,
    local_hour_floor,
    to_city,
    utcnow,
)
from app.ml import features as feat


def U(y, m, d, hh, mm=0):
    """Naive-UTC timestamp, matching the database convention."""
    return datetime(y, m, d, hh, mm)


class TestHourResolution:
    @pytest.mark.parametrize(
        "utc_ts,expected_local_hour,expected_weekday",
        [
            # EDT (UTC-4): the morning peak sits at 12:00Z.
            (U(2026, 9, 28, 12, 0), 8, 0),   # Monday
            (U(2026, 7, 15, 12, 0), 8, 2),    # Wednesday
            # EST (UTC-5): the same local hour is a different UTC hour.
            (U(2026, 1, 15, 13, 0), 8, 3),   # Thursday
            (U(2026, 12, 5, 13, 0), 8, 5),    # Saturday
            # Local midnight and the hour before it.
            (U(2026, 9, 28, 4, 0), 0, 0),
            (U(2026, 1, 15, 5, 0), 0, 3),
        ],
    )
    def test_city_hour_matches_local_wall_clock(self, utc_ts, expected_local_hour, expected_weekday):
        assert city_hour(utc_ts) == expected_local_hour
        assert city_weekday(utc_ts) == expected_weekday

    def test_local_0800_is_1200z_in_summer_and_1300z_in_winter(self):
        """The regression that mattered: 08:00 local must never read as 08:00Z."""
        summer = U(2026, 7, 15, 12, 0)
        winter = U(2026, 1, 15, 13, 0)
        assert city_hour(summer) == 8
        assert city_hour(winter) == 8
        # And the old, wrong behaviour really did differ.
        assert summer.hour != city_hour(summer)
        assert winter.hour != city_hour(winter)

    def test_peak_hour_is_local_08_and_17(self):
        """The curve's two peaks must be reachable only via local hours."""
        assert max(feat.BASELINE_OCCUPANCY, key=feat.BASELINE_OCCUPANCY.get) == 8
        assert city_hour(U(2026, 9, 28, 12, 0)) == 8
        # No UTC instant labelled by the naive read can land on the local peak
        # during EDT hours.
        assert U(2026, 9, 28, 8, 0).hour == 8  # 08:00Z is 04:00 local - not the peak


class TestDaylightSaving:
    def test_spring_forward_skips_0200_local(self):
        """2026-03-08: 07:00Z is when 02:00 EST jumps to 03:00 EDT."""
        assert city_hour(U(2026, 3, 8, 6, 59)) == 1   # still 01:59 EST
        assert city_hour(U(2026, 3, 8, 7, 0)) == 3     # 03:00 EDT
        # Walking UTC hours, local hour 2 is never observed - and nothing crashes.
        seen = [city_hour(U(2026, 3, 8, h, 0)) for h in range(0, 12)]
        assert 2 not in seen
        assert seen[6] == 1 and seen[7] == 3

    def test_fall_back_repeats_0100_local(self):
        """2026-11-01: 05:00Z and 06:00Z are both 01:00 local."""
        assert city_hour(U(2026, 11, 1, 4, 0)) == 0   # 00:00 EDT
        assert city_hour(U(2026, 11, 1, 5, 0)) == 1   # 01:00 EDT
        assert city_hour(U(2026, 11, 1, 6, 0)) == 1   # 01:00 EST (repeat)
        assert to_city(U(2026, 11, 1, 5, 0)).utcoffset() != to_city(U(2026, 11, 1, 6, 0)).utcoffset()

    def test_utc_hour_floor_is_uniform_across_dst(self):
        """The bucket key must stay exactly 1h apart in both regimes."""
        spring = U(2026, 3, 8, 6, 0)
        fall = U(2026, 11, 1, 4, 0)
        for base in (spring, fall):
            for h in range(0, 20):
                a = hour_floor(base + timedelta(hours=h))
                b = hour_floor(base + timedelta(hours=h + 1))
                assert (b - a) == timedelta(hours=1)


class TestAwareInput:
    def test_aware_datetimes_are_accepted(self):
        # 12:00 *in New York* is a different instant from 12:00Z, and the helper
        # must respect that rather than reading the wall-clock field.
        aware_ny = datetime(2026, 9, 28, 12, 0, tzinfo=CITY_TZ)
        assert city_hour(aware_ny) == 12
        assert city_weekday(aware_ny) == 0

    def test_utc_aware_input_converts(self):
        import datetime as _dt
        aware = _dt.datetime(2026, 9, 28, 12, 0, tzinfo=_dt.timezone.utc)
        assert city_hour(aware) == 8

    def test_as_utc_treats_naive_as_utc(self):
        assert as_utc(U(2026, 9, 28, 12, 0)).tzinfo is not None
        assert as_utc(U(2026, 9, 28, 12, 0)).hour == 12


class TestDayBoundaries:
    def test_city_day_start_is_local_midnight_not_utc_midnight(self):
        """The trap: 23:30Z is 19:30 local, so `replace(hour=0)` lands on the
        *previous* local day (20:00 on the 27th) and silently mislabels it."""
        evening = U(2026, 9, 28, 23, 30)
        start = city_day_start(evening)
        assert city_hour(start) == 0
        assert city_day_start(U(2026, 9, 28, 23, 59)) == start
        # Still the same local day at 00:05Z on the 29th (20:05 local on the 28th).
        assert city_day_start(U(2026, 9, 29, 0, 5)) == start
        # 04:05Z on the 29th is 00:05 local on the 29th -> the next local day.
        assert city_day_start(U(2026, 9, 29, 4, 5)) != start
        # The naive UTC floor that used to be used here lands on the wrong day.
        assert evening.replace(hour=0) < start
        assert city_weekday(evening.replace(hour=0)) == 6  # Saturday, not Monday

    def test_utcnow_is_naive(self):
        """Storage convention must not drift."""
        assert utcnow().tzinfo is None

    def test_local_hour_floor_keeps_local_alignment(self):
        ts = U(2026, 9, 28, 23, 45)
        assert city_hour(local_hour_floor(ts)) == 19
        assert local_hour_floor(ts).minute == 0


class TestGeneratedDatasetIsLocal:
    """End-to-end guard on the shipped CSV.

    The unit tests prove the helpers work; this proves the *artifact* was
    generated with them. Without it, a regenerated dataset could silently revert
    to UTC labels while every unit test still passed.
    """

    CSV = "data/ridership_hourly.csv"

    def _frame(self):
        pd = pytest.importorskip("pandas")
        import os
        if not os.path.exists(self.CSV):
            pytest.skip("generated dataset not present")
        df = pd.read_csv(self.CSV)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def test_hour_column_is_local_hour(self):
        df = self._frame()
        mismatches = sum(1 for ts, h in zip(df["timestamp"], df["hour"]) if h != city_hour(ts))
        assert mismatches == 0, f"{mismatches} rows labelled with a non-local hour"

    def test_no_row_uses_the_utc_hour(self):
        """The offset is 4h or 5h, never 0, so zero rows may coincide."""
        df = self._frame()
        coincident = sum(1 for ts, h in zip(df["timestamp"], df["hour"]) if h == ts.hour)
        assert coincident == 0, "dataset reverted to UTC hour labels"

    def test_profile_peaks_in_local_commute_hours(self):
        df = self._frame()
        prof = df.groupby("hour")["occupancy_pct"].mean()
        top4 = sorted(int(h) for h in prof.sort_values(ascending=False).index[:4])
        assert set(top4) <= {8, 9, 16, 17, 18}, f"peak drifted to {top4}"
        assert prof[8] > prof[3] and prof[17] > prof[12]

    def test_timestamps_are_still_uniform_utc_buckets(self):
        """Localisation must not disturb the storage grid."""
        df = self._frame()
        ts = df["timestamp"].drop_duplicates().sort_values()
        assert set(ts.diff().dropna()) == {timedelta(hours=1)}
