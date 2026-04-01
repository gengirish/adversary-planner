"""Stateless FastAPI backend for Adversary Planner — Vercel serverless."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adversary_planner.models import Target, CampaignState, TechniqueState
from adversary_planner.planner import BayesianPlanner
from adversary_planner.catalog import (
    get_techniques,
    get_technique,
    FAMILIES,
    BASELINES,
    GARAK_PROBE_MAP,
    get_family_for_technique,
)
from adversary_planner.calibration import calibrate, CalibrationResult
from adversary_planner.mapping import (
    get_owasp_coverage,
    get_nist_coverage,
    get_attack_surface_coverage,
)
from adversary_planner.importer import import_garak_report

app = FastAPI(title="Adversary Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class InitRequest(BaseModel):
    target: dict[str, Any]
    name: str


class StateRequest(BaseModel):
    state: dict[str, Any]


class RecommendRequest(BaseModel):
    state: dict[str, Any]
    count: int = 5
    diversify: bool = True


class ImportRequest(BaseModel):
    state: dict[str, Any]
    report_content: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _rebuild_planner(technique_states: dict[str, Any]) -> BayesianPlanner:
    planner = BayesianPlanner()
    planner.load_states(technique_states)
    return planner


def _tested_ids(technique_states: dict[str, Any]) -> set[str]:
    return {
        tid
        for tid, s in technique_states.items()
        if s.get("observations", 0) > 0
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "engine": "adversary-planner"}


@app.get("/api/techniques")
async def list_techniques():
    return [
        {
            "id": t.id,
            "name": t.name,
            "family": t.family,
            "description": t.description,
            "atlas_tactic": t.atlas_tactic,
            "atlas_technique": t.atlas_technique,
            "owasp_categories": t.owasp_categories,
            "nist_functions": t.nist_functions,
            "garak_probes": t.garak_probes,
            "related_techniques": t.related_techniques,
        }
        for t in get_techniques()
    ]


@app.get("/api/families")
async def list_families():
    techs = get_techniques()
    return [
        {
            "name": name,
            "description": desc,
            "count": sum(1 for t in techs if t.family == name),
            "baseline": BASELINES.get(name, {}),
        }
        for name, desc in sorted(FAMILIES.items())
    ]


@app.post("/api/campaign/init")
async def init_campaign(req: InitRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Campaign name is required")

    try:
        target = Target.from_dict(req.target)
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid target config: {exc}")

    planner = BayesianPlanner()
    planner.initialize(target)

    state = CampaignState(
        name=req.name.strip(),
        adaptive=True,
        target=req.target,
        technique_states=planner.get_state_dicts(),
    )

    return {"state": state.to_dict()}


@app.post("/api/campaign/recommend")
async def recommend(req: RecommendRequest):
    ts = req.state.get("technique_states", {})
    if not ts:
        raise HTTPException(status_code=400, detail="No technique states in campaign")

    planner = _rebuild_planner(ts)
    recs = planner.recommend(n=req.count, diversify=req.diversify)
    phase = planner.get_phase()

    return {
        "recommendations": [
            {
                "technique_id": r.technique_id,
                "technique_name": r.technique_name,
                "family": r.family,
                "sampled_score": r.sampled_score,
                "posterior_mean": r.posterior_mean,
                "uncertainty": r.uncertainty,
                "reason": r.reason,
                "suggested_probes": r.suggested_probes,
            }
            for r in recs
        ],
        "phase": phase,
    }


@app.post("/api/campaign/import")
async def import_report(req: ImportRequest):
    if not req.report_content.strip():
        raise HTTPException(status_code=400, detail="Report content is empty")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as f:
        f.write(req.report_content)
        tmp_path = f.name

    try:
        result = import_garak_report(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse report: {exc}")
    finally:
        os.unlink(tmp_path)

    planner = _rebuild_planner(req.state.get("technique_states", {}))

    for tech_id, counts in result.technique_results.items():
        planner.update(tech_id, counts["successes"], counts["failures"])

    state = dict(req.state)
    state["technique_states"] = planner.get_state_dicts()

    round_num = len(state.get("rounds", [])) + 1
    now = datetime.now().isoformat()
    round_record = {
        "round_number": round_num,
        "timestamp": now,
        "source": "garak",
        "techniques_updated": list(result.technique_results.keys()),
        "total_successes": sum(
            c["successes"] for c in result.technique_results.values()
        ),
        "total_failures": sum(
            c["failures"] for c in result.technique_results.values()
        ),
    }
    state.setdefault("rounds", []).append(round_record)
    state["updated"] = now

    return {
        "state": state,
        "round": round_record,
        "import_summary": {
            "total_attempts": result.total_attempts,
            "total_mapped": result.total_mapped,
            "techniques_hit": len(result.technique_results),
            "unmapped_probes": result.unmapped_probes,
        },
    }


@app.post("/api/campaign/calibrate")
async def calibrate_campaign(req: StateRequest):
    ts = req.state.get("technique_states", {})
    calibrations: list[dict] = []

    for tid, s in ts.items():
        obs = s.get("observations", 0)
        if obs == 0:
            continue
        asr = s.get("successes", 0) / obs
        family = get_family_for_technique(tid) or "unknown"
        c = calibrate(tid, family, asr)
        calibrations.append({
            "technique_id": c.technique_id,
            "family": c.family,
            "observed_asr": round(c.observed_asr, 4),
            "baseline_mean": c.baseline_mean,
            "baseline_std": c.baseline_std,
            "z_score": c.z_score,
            "interpretation": c.interpretation,
            "severity": c.severity,
            "baseline_source": c.baseline_source,
        })

    calibrations.sort(key=lambda x: x["z_score"], reverse=True)
    return {"calibrations": calibrations}


@app.post("/api/campaign/coverage")
async def coverage(req: StateRequest):
    tested = _tested_ids(req.state.get("technique_states", {}))
    return {
        "owasp": get_owasp_coverage(tested),
        "nist": get_nist_coverage(tested),
        "attack_surface": get_attack_surface_coverage(tested),
    }
