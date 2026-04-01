"""Shared fixtures for adversary planner tests."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from adversary_planner.models import Target, TechniqueState, CampaignState
from adversary_planner.planner import BayesianPlanner
from adversary_planner.campaign import CampaignManager


@pytest.fixture
def sample_target() -> Target:
    """Minimal target for testing."""
    return Target(
        name="Test Chatbot",
        target_type="chatbot",
        access_level="black_box",
        goals=["jailbreak", "extraction"],
        has_moderation=True,
        has_input_filtering=True,
    )


@pytest.fixture
def sample_target_yaml(tmp_path) -> Path:
    """Write a target YAML file and return its path."""
    target_file = tmp_path / "target.yaml"
    target_file.write_text(
        "name: Test Chatbot\n"
        "target_type: chatbot\n"
        "access_level: black_box\n"
        "goals: [jailbreak, extraction]\n"
        "defenses:\n"
        "  has_moderation: true\n"
        "  has_input_filtering: true\n"
    )
    return target_file


@pytest.fixture
def initialized_planner(sample_target) -> BayesianPlanner:
    """A BayesianPlanner with posteriors initialized from sample target."""
    planner = BayesianPlanner()
    planner.initialize(sample_target)
    return planner


@pytest.fixture
def campaign_manager(tmp_path) -> CampaignManager:
    """CampaignManager writing to a temporary directory."""
    return CampaignManager(base_dir=tmp_path / "campaigns")


@pytest.fixture
def active_campaign(campaign_manager, sample_target_yaml) -> CampaignManager:
    """CampaignManager with an already-created campaign."""
    campaign_manager.create(sample_target_yaml, name="test-campaign")
    return campaign_manager


@pytest.fixture
def sample_garak_report(tmp_path) -> Path:
    """Write a synthetic garak JSONL report and return its path."""
    report = tmp_path / "report.jsonl"
    lines = [
        json.dumps({"entry_type": "init", "garak_version": "0.14.0",
                     "start_time": "2026-01-01T00:00:00", "run": "test-001"}),
        json.dumps({"entry_type": "eval", "probe": "probes.dan.Dan_6_0",
                     "detector": "detectors.dan.DAN",
                     "passed": 12, "fails": 8, "total_evaluated": 20}),
        json.dumps({"entry_type": "eval", "probe": "probes.encoding.InjectBase64",
                     "detector": "detectors.encoding.DecodeDetect",
                     "passed": 5, "fails": 15, "total_evaluated": 20}),
        json.dumps({"entry_type": "eval", "probe": "probes.promptinject.HijackHateHumansMini",
                     "detector": "detectors.promptinject.AttackRogueString",
                     "passed": 18, "fails": 2, "total_evaluated": 20}),
        json.dumps({"entry_type": "completion", "end_time": "2026-01-01T00:15:00",
                     "run": "test-001"}),
    ]
    report.write_text("\n".join(lines) + "\n")
    return report
