"""Data models for adversary planner."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Target:
    name: str
    target_type: str  # chatbot, agent, api, embedding, rag
    access_level: str  # black_box, gray_box, white_box
    goals: list[str] = field(default_factory=lambda: ["jailbreak"])
    max_queries: int = 1000
    stealth_priority: str = "moderate"  # low, moderate, high
    has_moderation: bool = False
    has_input_filtering: bool = False
    has_output_filtering: bool = False
    has_rate_limiting: bool = False
    has_tools: bool = False
    has_rag: bool = False
    model_provider: str = "unknown"

    @classmethod
    def from_dict(cls, data: dict) -> Target:
        constraints = data.get("constraints", {})
        defenses = data.get("defenses", {})
        capabilities = data.get("capabilities", {})
        return cls(
            name=data["name"],
            target_type=data.get("target_type", "chatbot"),
            access_level=data.get("access_level", "black_box"),
            goals=data.get("goals", ["jailbreak"]),
            max_queries=constraints.get("max_queries", 1000),
            stealth_priority=constraints.get("stealth_priority", "moderate"),
            has_moderation=defenses.get("has_moderation", False),
            has_input_filtering=defenses.get("has_input_filtering", False),
            has_output_filtering=defenses.get("has_output_filtering", False),
            has_rate_limiting=defenses.get("has_rate_limiting", False),
            has_tools=capabilities.get("has_tools", False),
            has_rag=capabilities.get("has_rag", False),
            model_provider=data.get("model_provider", "unknown"),
        )


@dataclass
class Technique:
    id: str
    name: str
    family: str
    description: str
    atlas_tactic: str = ""
    atlas_technique: str = ""
    access_level: str = "black_box"
    owasp_categories: list[str] = field(default_factory=list)
    nist_functions: list[str] = field(default_factory=list)
    related_techniques: list[str] = field(default_factory=list)
    garak_probes: list[str] = field(default_factory=list)


@dataclass
class TechniqueState:
    technique_id: str
    alpha: float = 2.0
    beta: float = 2.0
    successes: int = 0
    failures: int = 0
    observations: int = 0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        total = self.alpha + self.beta
        return (self.alpha * self.beta) / (total ** 2 * (total + 1))

    @property
    def asr(self) -> Optional[float]:
        """Observed attack success rate."""
        if self.observations == 0:
            return None
        return self.successes / self.observations

    def to_dict(self) -> dict:
        return {
            "technique_id": self.technique_id,
            "alpha": self.alpha,
            "beta": self.beta,
            "successes": self.successes,
            "failures": self.failures,
            "observations": self.observations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TechniqueState:
        return cls(**data)


@dataclass
class RoundRecord:
    round_number: int
    timestamp: str
    source: str  # "garak", "pyrit", "manual"
    techniques_updated: list[str] = field(default_factory=list)
    total_successes: int = 0
    total_failures: int = 0
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RoundRecord:
        return cls(**data)


@dataclass
class CampaignState:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    adaptive: bool = True
    target: dict = field(default_factory=dict)
    technique_states: dict[str, dict] = field(default_factory=dict)
    rounds: list[dict] = field(default_factory=list)
    status: str = "active"  # active, completed, paused

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created": self.created,
            "updated": self.updated,
            "adaptive": self.adaptive,
            "target": self.target,
            "technique_states": self.technique_states,
            "rounds": self.rounds,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CampaignState:
        return cls(**data)


@dataclass
class ImportResult:
    source: str
    technique_results: dict[str, dict]  # technique_id -> {successes, failures}
    unmapped_probes: list[str] = field(default_factory=list)
    total_attempts: int = 0
    total_mapped: int = 0
