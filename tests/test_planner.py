"""Tests for the Bayesian planner engine."""

from __future__ import annotations

import pytest

from adversary_planner.planner import BayesianPlanner, Recommendation
from adversary_planner.models import TechniqueState


class TestBayesianPlannerInit:
    """Test planner initialization from target profiles."""

    def test_initialize_creates_states_for_all_techniques(self, initialized_planner):
        assert len(initialized_planner.states) == 49

    def test_all_states_have_positive_alpha_beta(self, initialized_planner):
        for tid, state in initialized_planner.states.items():
            assert state.alpha >= 1.0, f"{tid} alpha < 1"
            assert state.beta >= 1.0, f"{tid} beta < 1"

    def test_states_have_zero_observations(self, initialized_planner):
        for state in initialized_planner.states.values():
            assert state.observations == 0
            assert state.successes == 0
            assert state.failures == 0


class TestBayesianUpdate:
    """Test posterior updates and spillover."""

    def test_update_increments_alpha_on_success(self, initialized_planner):
        old_alpha = initialized_planner.states["T0001"].alpha
        initialized_planner.update("T0001", successes=5, failures=0)
        assert initialized_planner.states["T0001"].alpha == old_alpha + 5

    def test_update_increments_beta_on_failure(self, initialized_planner):
        old_beta = initialized_planner.states["T0001"].beta
        initialized_planner.update("T0001", successes=0, failures=3)
        assert initialized_planner.states["T0001"].beta == old_beta + 3

    def test_update_tracks_observations(self, initialized_planner):
        initialized_planner.update("T0001", successes=4, failures=6)
        state = initialized_planner.states["T0001"]
        assert state.observations == 10
        assert state.successes == 4
        assert state.failures == 6

    def test_spillover_updates_siblings(self, initialized_planner):
        old_alpha_sibling = initialized_planner.states["T0002"].alpha
        initialized_planner.update("T0001", successes=10, failures=0, spillover=0.3)
        new_alpha_sibling = initialized_planner.states["T0002"].alpha
        assert new_alpha_sibling == pytest.approx(old_alpha_sibling + 10 * 0.3)

    def test_spillover_does_not_affect_other_families(self, initialized_planner):
        old_alpha = initialized_planner.states["T0011"].alpha  # encoding family
        initialized_planner.update("T0001", successes=10, failures=0)  # jailbreak
        assert initialized_planner.states["T0011"].alpha == old_alpha

    def test_update_unknown_technique_is_noop(self, initialized_planner):
        initialized_planner.update("TXXX_NONEXISTENT", successes=5, failures=5)


class TestThompsonSampling:
    """Test the recommendation engine."""

    def test_recommend_returns_requested_count(self, initialized_planner):
        recs = initialized_planner.recommend(n=5)
        assert len(recs) == 5

    def test_recommend_returns_recommendation_objects(self, initialized_planner):
        recs = initialized_planner.recommend(n=3)
        for r in recs:
            assert isinstance(r, Recommendation)
            assert r.technique_id
            assert r.technique_name
            assert r.family
            assert 0.0 <= r.sampled_score <= 1.0

    def test_diversify_limits_one_per_family(self, initialized_planner):
        recs = initialized_planner.recommend(n=10, diversify=True)
        families = [r.family for r in recs]
        assert len(families) == len(set(families))

    def test_no_diversify_allows_same_family(self, initialized_planner):
        recs = initialized_planner.recommend(n=49, diversify=False)
        families = [r.family for r in recs]
        assert len(families) > len(set(families))

    def test_exclude_removes_techniques(self, initialized_planner):
        exclude = {"T0001", "T0002", "T0003"}
        recs = initialized_planner.recommend(n=49, diversify=False, exclude=exclude)
        rec_ids = {r.technique_id for r in recs}
        assert rec_ids.isdisjoint(exclude)

    def test_high_success_technique_ranks_higher_on_average(self, initialized_planner):
        initialized_planner.update("T0011", successes=50, failures=2)
        scores = []
        for _ in range(100):
            recs = initialized_planner.recommend(n=49, diversify=False)
            for i, r in enumerate(recs):
                if r.technique_id == "T0011":
                    scores.append(i)
                    break
        avg_rank = sum(scores) / len(scores)
        assert avg_rank < 10, f"T0011 avg rank {avg_rank} should be near top after 50 successes"


class TestPlannerPhase:
    """Test campaign phase detection."""

    def test_initial_phase_is_exploration(self, initialized_planner):
        assert initialized_planner.get_phase() == "exploration"

    def test_phase_shifts_after_many_observations(self, initialized_planner):
        for tid in list(initialized_planner.states.keys()):
            initialized_planner.update(tid, successes=20, failures=20)
        phase = initialized_planner.get_phase()
        assert phase in ("transition", "exploitation")


class TestStateSerialisation:
    """Test round-trip serialization of planner state."""

    def test_get_and_load_state_round_trip(self, initialized_planner):
        initialized_planner.update("T0001", successes=3, failures=7)
        state_dicts = initialized_planner.get_state_dicts()

        new_planner = BayesianPlanner()
        new_planner.load_states(state_dicts)

        orig = initialized_planner.states["T0001"]
        loaded = new_planner.states["T0001"]
        assert loaded.alpha == orig.alpha
        assert loaded.beta == orig.beta
        assert loaded.observations == orig.observations
