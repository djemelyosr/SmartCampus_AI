"""Date helpers. Validity periods of official information are calendar dates in Tunisia."""

from datetime import date, datetime, timedelta, timezone

TUNIS = timezone(timedelta(hours=1))  # Africa/Tunis is UTC+1 all year (no daylight saving time)


def tn_today() -> date:
    return datetime.now(TUNIS).date()
