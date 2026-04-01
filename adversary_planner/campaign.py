"""Campaign lifecycle management with persistent state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

from .models import CampaignState, Target, RoundRecord, ImportResult
from .planner import BayesianPlanner, Recommendation
from .calibration import calibrate_batch, CalibrationResult
from .catalog import get_techniques, get_family_for_technique
from .exceptions import (
    CampaignNotFoundError,
    CampaignNotLoadedError,
    TargetFileError,
    ValidationError,
)

CAMPAIGNS_DIR = Path(".adversary_planner") / "campaigns"


class CampaignManager:
    """Orchestrates campaign creation, state persistence, and round execution."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or CAMPAIGNS_DIR
        self.state: CampaignState | None = None
        self.planner = BayesianPlanner()
        self.target: Target | None = None

    def create(
        self,
        target_path: str | Path,
        name: str,
        adaptive: bool = True,
    ) -> CampaignState:
        """Create a new campaign from a target YAML file."""
        if not name or not name.strip():
            raise ValidationError("Campaign name cannot be empty", field="name")

        target_path = Path(target_path)
        if not target_path.exists():
            raise TargetFileError(str(target_path), "file does not exist")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                target_data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise TargetFileError(str(target_path), f"invalid YAML: {exc}") from exc

        if not isinstance(target_data, dict):
            raise TargetFileError(str(target_path), "expected a YAML mapping at top level")
        if "name" not in target_data:
            raise TargetFileError(str(target_path), "missing required field 'name'")

        self.target = Target.from_dict(target_data)
        self.planner.initialize(self.target)

        self.state = CampaignState(
            name=name.strip(),
            adaptive=adaptive,
            target=target_data,
            technique_states=self.planner.get_state_dicts(),
        )

        self._save()
        return self.state

    def load(self, campaign_id: str) -> CampaignState:
        """Load an existing campaign by ID."""
        if not campaign_id or not campaign_id.strip():
            raise ValidationError("Campaign ID cannot be empty", field="campaign_id")

        state_path = self.base_dir / campaign_id / "state.json"
        if not state_path.exists():
            raise CampaignNotFoundError(campaign_id)

        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.state = CampaignState.from_dict(data)
        self.target = Target.from_dict(self.state.target)
        self.planner.load_states(self.state.technique_states)
        return self.state

    def list_campaigns(self) -> list[dict]:
        """List all campaigns with summary info."""
        if not self.base_dir.exists():
            return []

        campaigns = []
        for campaign_dir in sorted(self.base_dir.iterdir()):
            state_file = campaign_dir / "state.json"
            if not state_file.exists():
                continue
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            campaigns.append({
                "id": data["id"],
                "name": data["name"],
                "status": data["status"],
                "created": data["created"],
                "rounds": len(data.get("rounds", [])),
                "target": data.get("target", {}).get("name", "Unknown"),
            })
        return campaigns

    def next_recommendations(
        self,
        count: int = 5,
        diversify: bool = True,
    ) -> list[Recommendation]:
        """Get next technique recommendations via Thompson Sampling."""
        if self.state is None:
            raise CampaignNotLoadedError()
        if count < 1:
            raise ValidationError("Recommendation count must be >= 1", field="count", value=count)
        return self.planner.recommend(n=count, diversify=diversify)

    def import_results(self, result: ImportResult) -> RoundRecord:
        """Import scan results and update posteriors."""
        if self.state is None:
            raise CampaignNotLoadedError()

        for tech_id, counts in result.technique_results.items():
            self.planner.update(
                tech_id,
                counts["successes"],
                counts["failures"],
            )

        round_num = len(self.state.rounds) + 1
        record = RoundRecord(
            round_number=round_num,
            timestamp=datetime.now().isoformat(),
            source=result.source,
            techniques_updated=list(result.technique_results.keys()),
            total_successes=sum(c["successes"] for c in result.technique_results.values()),
            total_failures=sum(c["failures"] for c in result.technique_results.values()),
        )

        self.state.rounds.append(record.to_dict())
        self.state.technique_states = self.planner.get_state_dicts()
        self.state.updated = datetime.now().isoformat()
        self._save()

        return record

    def get_calibrations(self) -> list[CalibrationResult]:
        """Run Z-score calibration on all techniques with observations."""
        if self.state is None:
            raise CampaignNotLoadedError()

        results_with_data = {}
        tech_families = {}

        for tech_id, state_dict in self.state.technique_states.items():
            obs = state_dict.get("observations", 0)
            if obs > 0:
                results_with_data[tech_id] = {
                    "successes": state_dict["successes"],
                    "failures": state_dict["failures"],
                }
                family = get_family_for_technique(tech_id)
                if family:
                    tech_families[tech_id] = family

        return calibrate_batch(results_with_data, tech_families)

    def get_tested_technique_ids(self) -> set[str]:
        """Return set of technique IDs that have been tested (observations > 0)."""
        if self.state is None:
            return set()
        return {
            tid for tid, sd in self.state.technique_states.items()
            if sd.get("observations", 0) > 0
        }

    def get_phase(self) -> str:
        return self.planner.get_phase()

    def _save(self) -> None:
        if self.state is None:
            return
        campaign_dir = self.base_dir / self.state.id
        campaign_dir.mkdir(parents=True, exist_ok=True)
        state_path = campaign_dir / "state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2)
