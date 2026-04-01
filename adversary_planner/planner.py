"""Bayesian attack planner with Thompson Sampling."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import TechniqueState, Target, Technique
from .catalog import BASELINES, get_techniques, build_family_map


SPILLOVER_FACTOR = 0.3
BASELINE_WEIGHT = 0.6
COMPATIBILITY_WEIGHT = 0.4
PRIOR_STRENGTH = 10  # pseudo-observations for baseline prior
COMPAT_STRENGTH = 5  # pseudo-observations for compatibility prior


@dataclass
class Recommendation:
    technique_id: str
    technique_name: str
    family: str
    sampled_score: float
    posterior_mean: float
    uncertainty: float
    reason: str
    suggested_probes: list[str] = field(default_factory=list)


class BayesianPlanner:
    """
    Maintains Beta(alpha, beta) posteriors for each technique and uses
    Thompson Sampling to recommend the next techniques to try.
    """

    def __init__(self):
        self.states: dict[str, TechniqueState] = {}
        self.family_map: dict[str, list[str]] = build_family_map()
        self.techniques: dict[str, Technique] = {
            t.id: t for t in get_techniques()
        }

    def initialize(self, target: Target) -> None:
        """Set initial posteriors from blended priors (baseline + compatibility)."""
        for tech_id, tech in self.techniques.items():
            baseline = BASELINES.get(tech.family, {"mean": 0.3, "std": 0.15})
            compat = self._compute_compatibility(tech, target)

            bl_alpha = baseline["mean"] * PRIOR_STRENGTH
            bl_beta = (1.0 - baseline["mean"]) * PRIOR_STRENGTH

            cp_alpha = compat * COMPAT_STRENGTH
            cp_beta = (1.0 - compat) * COMPAT_STRENGTH

            alpha = BASELINE_WEIGHT * bl_alpha + COMPATIBILITY_WEIGHT * cp_alpha
            beta = BASELINE_WEIGHT * bl_beta + COMPATIBILITY_WEIGHT * cp_beta

            self.states[tech_id] = TechniqueState(
                technique_id=tech_id,
                alpha=max(alpha, 1.0),
                beta=max(beta, 1.0),
            )

    def load_states(self, state_dicts: dict[str, dict]) -> None:
        """Restore posteriors from serialized campaign state."""
        self.states = {
            tid: TechniqueState.from_dict(sd)
            for tid, sd in state_dicts.items()
        }

    def update(
        self,
        technique_id: str,
        successes: int,
        failures: int,
        spillover: float = SPILLOVER_FACTOR,
    ) -> None:
        """Update posterior for a technique and propagate spillover to siblings."""
        if technique_id not in self.states:
            return

        state = self.states[technique_id]
        state.alpha += successes
        state.beta += failures
        state.successes += successes
        state.failures += failures
        state.observations += successes + failures

        tech = self.techniques.get(technique_id)
        if tech is None:
            return

        siblings = self.family_map.get(tech.family, [])
        for sib_id in siblings:
            if sib_id != technique_id and sib_id in self.states:
                self.states[sib_id].alpha += successes * spillover
                self.states[sib_id].beta += failures * spillover

    def recommend(
        self,
        n: int = 5,
        exclude: set[str] | None = None,
        diversify: bool = True,
    ) -> list[Recommendation]:
        """
        Thompson Sampling: draw one sample from each technique's Beta posterior,
        rank by sampled value, return top N.

        When diversify=True, at most one technique per family is returned to
        encourage exploration breadth.
        """
        exclude = exclude or set()
        samples: list[tuple[str, float]] = []

        for tech_id, state in self.states.items():
            if tech_id in exclude:
                continue
            sample = random.betavariate(state.alpha, state.beta)
            samples.append((tech_id, sample))

        samples.sort(key=lambda x: x[1], reverse=True)

        results: list[Recommendation] = []
        seen_families: set[str] = set()

        for tech_id, sampled in samples:
            if len(results) >= n:
                break

            tech = self.techniques.get(tech_id)
            if tech is None:
                continue

            if diversify and tech.family in seen_families:
                continue
            seen_families.add(tech.family)

            state = self.states[tech_id]
            uncertainty = state.variance ** 0.5
            reason = self._explain(state, sampled, uncertainty)

            results.append(Recommendation(
                technique_id=tech_id,
                technique_name=tech.name,
                family=tech.family,
                sampled_score=round(sampled, 4),
                posterior_mean=round(state.mean, 4),
                uncertainty=round(uncertainty, 4),
                reason=reason,
                suggested_probes=tech.garak_probes,
            ))

        return results

    def get_state_dicts(self) -> dict[str, dict]:
        """Serialize all posteriors for campaign persistence."""
        return {tid: s.to_dict() for tid, s in self.states.items()}

    def get_phase(self) -> str:
        """
        Determine campaign phase based on average posterior uncertainty.
        High uncertainty -> exploration, low -> exploitation.
        """
        if not self.states:
            return "exploration"

        avg_var = sum(s.variance for s in self.states.values()) / len(self.states)
        avg_std = avg_var ** 0.5

        if avg_std > 0.15:
            return "exploration"
        elif avg_std > 0.08:
            return "transition"
        else:
            return "exploitation"

    def _compute_compatibility(self, tech: Technique, target: Target) -> float:
        """
        Heuristic compatibility score [0, 1] for a technique against a target.
        Higher = more likely to succeed.
        """
        score = 0.5

        if tech.access_level == "white_box" and target.access_level == "black_box":
            return 0.05

        if tech.family == "encoding" and target.has_input_filtering:
            score -= 0.15
        if tech.family == "toxicity" and target.has_moderation:
            score -= 0.20
        if tech.family == "toxicity" and target.has_output_filtering:
            score -= 0.15
        if tech.family == "agent_abuse" and not target.has_tools:
            score -= 0.30
        if tech.family == "rag_poisoning" and not target.has_rag:
            score -= 0.35
        if tech.family == "jailbreak" and not target.has_moderation:
            score += 0.15
        if tech.family == "data_extraction" and target.access_level == "black_box":
            score -= 0.10
        if tech.family in ("social_engineering", "jailbreak"):
            if target.target_type in ("chatbot", "assistant"):
                score += 0.10
        if tech.family == "automated_red_team":
            score += 0.05

        return max(0.05, min(0.95, score))

    def _explain(self, state: TechniqueState, sampled: float, uncertainty: float) -> str:
        if state.observations == 0:
            if uncertainty > 0.15:
                return "High uncertainty — untested, worth exploring"
            return "Prior suggests moderate success probability"

        if state.asr is not None and state.asr > 0.5:
            return f"Observed {state.asr:.0%} ASR — exploit further"
        elif state.asr is not None and state.asr > 0.2:
            return f"Partial success ({state.asr:.0%} ASR) — deeper probing may yield results"
        elif uncertainty > 0.12:
            return "Low success so far but high uncertainty — more data needed"
        else:
            return "Low success probability — consider deprioritizing"
