"""Time handling for a single-city transit domain.

Storage convention: **every timestamp persisted in the database is naive UTC.**
That is deliberate — UTC has no DST gaps, so hourly buckets are always exactly one
hour apart and range scans stay correct forever.

The cost of that convention is that a naive UTC value does *not* carry a
meaningful hour-of-day for the city the app models. `BASELINE_OCCUPANCY` describes
a New York commute: 08:00 is the morning peak, 03:00 is the small hours. Reading
`timestamp.hour` off a UTC value therefore put the morning peak at 04:00 local
and made every chart, forecast and alert describe the wrong time of day.

So the rule this module enforces is:

* **store** UTC, **never** local;
* **interpret** every hour-of-day / day-of-week through :func:`city_hour` and
  :func:`city_weekday`, which convert through the city's IANA zone.

Keeping the conversion in one place is what stops the model, the generator and
the read paths from disagreeing about what "08:00" means.
"""

from datetime import date, datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

# IANA zone for the modelled network. Not a fixed -05:00 offset: America/New_York
# alternates between EST (-05:00) and EDT (-04:00), and the ridership window spans
# a DST transition, so a hardcoded offset would mislabel one of the two days.
CITY_TZ = ZoneInfo("America/New_York")

CITY_NAME = "America/New_York"


def utcnow() -> datetime:
    """Naive UTC "now" (identical value to the removed ``datetime.utcnow()``),
    derived explicitly from :data:`datetime.timezone.utc`. Stored DB timestamps
    remain naive-UTC, so comparisons stay byte-for-byte unchanged."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc(moment: datetime) -> datetime:
    """Coerce a datetime to an aware UTC instant.

    Accepts naive values (the database convention, assumed UTC) and aware values
    (converted), so callers never have to care which they were handed.
    """
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def to_city(moment: datetime) -> datetime:
    """Interpret a (naive-UTC or aware) moment in the city's local zone."""
    return as_utc(moment).astimezone(CITY_TZ)


def city_hour(moment: datetime) -> int:
    """Local hour-of-day (0-23) for a stored naive-UTC timestamp.

    This is the *only* correct way to index :data:`~app.ml.features.BASELINE_OCCUPANCY`.
    """
    return to_city(moment).hour


def city_weekday(moment: datetime) -> int:
    """Local day-of-week (Mon=0 .. Sun=6) for a stored naive-UTC timestamp."""
    return to_city(moment).weekday()


def city_date(moment: datetime) -> date:
    """Local calendar date for a stored naive-UTC timestamp."""
    return to_city(moment).date()


def is_city_weekend(moment: datetime) -> bool:
    return city_weekday(moment) >= 5


def city_day_start(moment: datetime) -> datetime:
    """Naive-UTC timestamp of 00:00 *local* time on `moment`'s local date.

    Used to build calendar-day plans. Note this is deliberately *not*
    ``moment.replace(hour=0)``: that would floor to midnight UTC, which is 19:00
    or 20:00 local and lands on the wrong day for most of the evening.
    """
    local = to_city(moment)
    return datetime.combine(local.date(), datetime.min.time(), tzinfo=CITY_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def hour_floor(moment: datetime | None = None) -> datetime:
    """Truncate to the containing UTC hour. UTC hours are exactly 1 hour apart in
    both DST regimes, so this stays correct year-round."""
    m = utcnow() if moment is None else as_utc(moment).replace(tzinfo=None)
    return m.replace(minute=0, second=0, microsecond=0)


def local_instant(day: date, hour: int, minute: int = 0) -> datetime:
    """Naive-UTC instant of a given *local* wall-clock date and time.

    The inverse of :func:`city_hour`/:func:`city_date`. Needed wherever a schedule
    or dataset is defined in local terms — "departures from 05:00 local" must not
    be written as ``datetime(..., 5)``, which is 05:00 **UTC** and four hours of
    clock off for a New York commuter. DST-correct because the offset comes from
    the zone database rather than a constant.
    """
    return datetime.combine(day, dtime(hour, minute), tzinfo=CITY_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def local_hour_floor(moment: datetime | None = None) -> datetime:
    """Truncate to the containing *local* hour, returned as naive UTC.

    Differs from :func:`hour_floor` only inside a DST transition, where local
    hours are 23 or 25 hours apart from their neighbour.
    """
    m = utcnow() if moment is None else moment
    local = to_city(m).replace(minute=0, second=0, microsecond=0)
    return local.astimezone(timezone.utc).replace(tzinfo=None)
