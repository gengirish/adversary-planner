"""Tests for campaign lifecycle management."""

from __future__ import annotations

import pytest

from adversary_planner.campaign import CampaignManager
from adversary_planner.importer import import_garak_report
from adversary_planner.exceptions import (
    CampaignNotFoundError,
    CampaignNotLoadedError,
    TargetFileError,
    ValidationError,
)


class TestCampaignCreation:
    """Test campaign create/load lifecycle."""

    def test_create_campaign_returns_state(self, campaign_manager, sample_target_yaml):
        state = campaign_manager.create(sample_target_yaml, name="test")
        assert state.name == "test"
        assert state.id
        assert state.status == "active"

    def test_create_campaign_initializes_technique_states(self, campaign_manager, sample_target_yaml):
        state = campaign_manager.create(sample_target_yaml, name="test")
        assert len(state.technique_states) == 49

    def test_create_strips_whitespace_from_name(self, campaign_manager, sample_target_yaml):
        state = campaign_manager.create(sample_target_yaml, name="  padded name  ")
        assert state.name == "padded name"

    def test_create_with_empty_name_raises(self, campaign_manager, sample_target_yaml):
        with pytest.raises(ValidationError, match="empty"):
            campaign_manager.create(sample_target_yaml, name="")

    def test_create_with_missing_file_raises(self, campaign_manager, tmp_path):
        with pytest.raises(TargetFileError, match="does not exist"):
            campaign_manager.create(tmp_path / "no_such.yaml", name="test")

    def test_create_with_invalid_yaml_raises(self, campaign_manager, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("key: [unterminated\n  - broken:\n")
        with pytest.raises(TargetFileError):
            campaign_manager.create(bad, name="test")

    def test_create_with_missing_name_field_raises(self, campaign_manager, tmp_path):
        no_name = tmp_path / "no_name.yaml"
        no_name.write_text("target_type: chatbot\n")
        with pytest.raises(TargetFileError, match="missing required field"):
            campaign_manager.create(no_name, name="test")

    def test_load_nonexistent_campaign_raises(self, campaign_manager):
        with pytest.raises(CampaignNotFoundError):
            campaign_manager.load("nonexistent-id")

    def test_load_empty_id_raises(self, campaign_manager):
        with pytest.raises(ValidationError, match="empty"):
            campaign_manager.load("")


class TestCampaignLoadAndPersist:
    """Test save/load round-trip."""

    def test_load_restores_state(self, active_campaign):
        cid = active_campaign.state.id
        mgr2 = CampaignManager(base_dir=active_campaign.base_dir)
        mgr2.load(cid)
        assert mgr2.state.name == "test-campaign"
        assert len(mgr2.state.technique_states) == 49

    def test_list_campaigns_shows_created(self, active_campaign):
        campaigns = active_campaign.list_campaigns()
        assert len(campaigns) == 1
        assert campaigns[0]["name"] == "test-campaign"


class TestCampaignOperations:
    """Test recommendations and imports on a loaded campaign."""

    def test_next_recommendations_without_load_raises(self, campaign_manager):
        with pytest.raises(CampaignNotLoadedError):
            campaign_manager.next_recommendations()

    def test_next_recommendations_returns_list(self, active_campaign):
        recs = active_campaign.next_recommendations(count=3)
        assert len(recs) == 3

    def test_import_results_creates_round(self, active_campaign, sample_garak_report):
        result = import_garak_report(sample_garak_report)
        record = active_campaign.import_results(result)
        assert record.round_number == 1
        assert record.total_successes + record.total_failures > 0

    def test_import_updates_posteriors(self, active_campaign, sample_garak_report):
        old_obs = sum(
            s.get("observations", 0) for s in active_campaign.state.technique_states.values()
        )
        result = import_garak_report(sample_garak_report)
        active_campaign.import_results(result)
        new_obs = sum(
            s.get("observations", 0) for s in active_campaign.state.technique_states.values()
        )
        assert new_obs > old_obs

    def test_multiple_rounds_increment(self, active_campaign, sample_garak_report):
        r1 = import_garak_report(sample_garak_report)
        active_campaign.import_results(r1)
        r2 = import_garak_report(sample_garak_report)
        record2 = active_campaign.import_results(r2)
        assert record2.round_number == 2
        assert len(active_campaign.state.rounds) == 2
