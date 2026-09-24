from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC "now" (identical value to the removed ``datetime.utcnow()``),
    derived explicitly from :data:`datetime.timezone.utc`. Stored DB timestamps
    remain naive-UTC, so comparisons stay byte-for-byte unchanged."""
    return datetime.now(timezone.utc).replace(tzinfo=None)