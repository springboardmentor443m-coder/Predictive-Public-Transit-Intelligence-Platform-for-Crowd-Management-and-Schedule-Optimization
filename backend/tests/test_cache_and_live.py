"""Cache-fallback and live-estimate contracts.

The cache tests pin a bug that was invisible in normal operation: when Redis was
unavailable the in-process fallback discarded the TTL, so every cached value
became permanent. The live-crowd snapshot was therefore computed once and served
unchanged forever — with no log line, no error, and a healthy-looking dashboard.
"Redis is down" is a routine event, so the fallback has to honour the same
contract as Redis.
"""

import time
from datetime import datetime, timedelta

import pytest

from app.core import cache as cache_mod
from app.services.crowd_service import intra_hour_estimate


@pytest.fixture(autouse=True)
def clean_local_cache(monkeypatch):
    """Force the Redis-less path and clear state between tests."""
    monkeypatch.setattr(cache_mod, "get_redis", lambda: None)
    cache_mod._local_cache.clear()
    yield
    cache_mod._local_cache.clear()


class TestLocalCacheHonoursTtl:
    def test_entry_expires_in_the_fallback(self):
        cache_mod.cache_set("k", {"v": 1}, ttl=30)
        assert cache_mod.cache_get("k") == {"v": 1}
        # Force expiry without sleeping 30s by rewinding the stored deadline.
        exp, payload = cache_mod._local_cache["k"]
        cache_mod._local_cache["k"] = (exp - 31, payload)
        assert cache_mod.cache_get("k") is None
        assert "k" not in cache_mod._local_cache

    def test_ttl_would_have_been_ignored_before(self):
        """Guard the specific regression: a past expiry must not be readable."""
        cache_mod.cache_set("k2", "value", ttl=1)
        cache_mod._local_cache["k2"] = (time.monotonic() - 1, '"value"')
        assert cache_mod.cache_get("k2") is None

    def test_zero_or_negative_ttl_does_not_cache(self):
        cache_mod.cache_set("k3", "value", ttl=0)
        assert cache_mod.cache_get("k3") is None

    def test_overwrite_replaces_value_and_deadline(self):
        cache_mod.cache_set("k4", "first", ttl=300)
        cache_mod.cache_set("k4", "second", ttl=1)
        assert cache_mod.cache_get("k4") == "second"
        exp, _ = cache_mod._local_cache["k4"]
        assert exp - time.monotonic() <= 1.5

    def test_local_cache_is_size_bounded(self):
        cap = cache_mod._LOCAL_CACHE_MAX
        try:
            cache_mod._LOCAL_CACHE_MAX = 50
            for i in range(500):
                cache_mod.cache_set(f"key{i}", i, ttl=300)
            assert len(cache_mod._local_cache) <= 50
            # The most recent write must survive eviction.
            assert cache_mod.cache_get("key499") == 499
        finally:
            cache_mod._LOCAL_CACHE_MAX = cap

    def test_delete_removes_local_entry(self):
        cache_mod.cache_set("k5", 1, ttl=60)
        cache_mod.cache_delete("k5")
        assert cache_mod.cache_get("k5") is None

    def test_redis_write_failure_falls_back_instead_of_losing_the_value(self, monkeypatch):
        class DeadRedis:
            def setex(self, *a, **k):
                raise ConnectionError("redis down")

            def get(self, *a, **k):
                raise ConnectionError("redis down")

            def delete(self, *a, **k):
                raise ConnectionError("redis down")

        monkeypatch.setattr(cache_mod, "get_redis", lambda: DeadRedis())
        cache_mod._local_cache.clear()
        cache_mod.cache_set("k6", {"v": 2}, ttl=60)
        assert cache_mod.cache_get("k6") == {"v": 2}


class TestIntraHourEstimate:
    def U(self, h, m=0, s=0):
        return datetime(2026, 9, 28, h, m, s)

    def test_advances_from_previous_hour_towards_current(self):
        start = self.U(12)
        occ, elapsed, est = intra_hour_estimate(1000, 2000, self.U(12, 30), start)
        assert elapsed == pytest.approx(0.5)
        assert occ == 1500
        assert est is True

    def test_is_bounded_by_the_two_measurements(self):
        start = self.U(12)
        for minute in (0, 15, 30, 45, 59):
            occ, _, _ = intra_hour_estimate(1000, 2000, self.U(12, minute), start)
            assert 1000 <= occ <= 2000

    def test_starts_at_previous_hour_level(self):
        occ, elapsed, _ = intra_hour_estimate(1000, 2000, self.U(12, 0), self.U(12))
        assert occ == 1000 and elapsed == 0.0

    def test_handles_a_decreasing_hour(self):
        occ, _, _ = intra_hour_estimate(2000, 1000, self.U(12, 30), self.U(12))
        assert occ == 1500

    def test_missing_previous_bucket_is_not_an_estimate(self):
        occ, elapsed, est = intra_hour_estimate(None, 1234, self.U(12, 30), self.U(12))
        assert occ == 1234 and est is False

    def test_elapsed_never_reaches_one(self):
        _, elapsed, _ = intra_hour_estimate(1000, 2000, self.U(12, 59, 59), self.U(12))
        assert 0 <= elapsed < 1.0

    def test_value_actually_moves_over_time(self):
        """The bug this exists for: consecutive polls must not be identical."""
        start = self.U(12)
        vals = [intra_hour_estimate(1000, 3000, self.U(12, m), start)[0] for m in (0, 10, 20, 30, 40, 50)]
        assert vals == sorted(vals)
        assert len(set(vals)) > 1
