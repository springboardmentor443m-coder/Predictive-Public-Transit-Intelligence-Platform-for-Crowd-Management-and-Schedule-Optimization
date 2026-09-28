"""Headway-recommendation honesty.

The optimizer used to pick its wording from the time of day alone, so a user
could read "current headway 6 min / recommended 15 min" beside "steady demand;
standard headway sufficient" — a proposed halving of service described as if
nothing needed doing. The direction of the change is what an operator acts on,
so it now drives both the wording and whether the item is escalated at all.
"""

import pytest

from app.services.scheduling_service import (
    classify_headway_action,
    compute_recommended_headway,
)


class TestComputeRecommendedHeadway:
    def test_is_always_within_a_serviceable_band(self):
        # Below ~3 min a line is not physically dispatchable; above ~15 min it is
        # no longer recognisable as trunk-route service.
        for demand in (0, 50, 500, 5_000, 50_000, 500_000):
            h = compute_recommended_headway(demand, train_capacity=1_248)
            assert 3 <= h <= 15

    def test_demand_above_zero_never_recommends_impossible_service(self):
        assert compute_recommended_headway(0) >= 3
        assert compute_recommended_headway(1) >= 3

    def test_higher_demand_never_yields_a_longer_headway(self):
        headways = [compute_recommended_headway(d) for d in (100, 1_000, 10_000, 100_000)]
        assert headways == sorted(headways, reverse=True)


class TestClassifyHeadwayAction:
    def test_tightening_service_escalates_and_explains(self):
        severity, reason, needs_action = classify_headway_action(8, 4, peak=True)
        assert needs_action is True
        assert severity == "high"
        assert "8 min" in reason and "4 min" in reason
        assert "4 min more frequent" in reason

    def test_longer_headway_is_reported_as_spare_capacity_not_a_recommendation(self):
        severity, reason, needs_action = classify_headway_action(6, 15, peak=False)
        assert needs_action is False
        assert severity == "low"
        assert "spare capacity" in reason
        # The old wording implied action was required.
        assert "sufficient" not in reason

    def test_matching_headway_needs_no_action_either_way(self):
        for peak in (True, False):
            severity, reason, needs_action = classify_headway_action(6, 6, peak=peak)
            assert needs_action is False
            assert severity == "info"
            assert "already matches" in reason

    def test_reason_always_names_both_headways(self):
        for current, recommended in ((3, 15), (15, 3), (7, 7)):
            _, reason, _ = classify_headway_action(current, recommended, peak=False)
            assert str(current) in reason and str(recommended) in reason

    def test_reason_never_contradicts_the_direction(self):
        # A "reduced headway recommended" string must never accompany a longer
        # recommended headway than the one already running.
        _, reason, _ = classify_headway_action(4, 12, peak=True)
        assert "reduced headway recommended" not in reason
        assert "tighten" not in reason
