"""Report generation for campaign results."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .campaign import CampaignManager
from .catalog import get_technique, FAMILIES
from .mapping import (
    get_owasp_coverage,
    get_nist_coverage,
    get_attack_surface_coverage,
    OWASP_LLM_TOP_10,
)


def generate_report(manager: CampaignManager, output_path: str | None = None) -> str:
    """Generate a Markdown campaign report."""
    state = manager.state
    if state is None:
        raise RuntimeError("No campaign loaded")

    calibrations = manager.get_calibrations()
    tested_ids = manager.get_tested_technique_ids()
    owasp = get_owasp_coverage(tested_ids)
    nist = get_nist_coverage(tested_ids)
    attack_surface = get_attack_surface_coverage(tested_ids)
    phase = manager.get_phase()

    lines: list[str] = []
    _w = lines.append

    # ── Header ─────────────────────────────────────────────────
    _w(f"# Campaign Report: {state.name}")
    _w("")
    _w(f"**Campaign ID:** `{state.id}`")
    _w(f"**Target:** {state.target.get('name', 'Unknown')}")
    _w(f"**Created:** {state.created[:10]}")
    _w(f"**Last Updated:** {state.updated[:10]}")
    _w(f"**Rounds Completed:** {len(state.rounds)}")
    _w(f"**Campaign Phase:** {phase.title()}")
    _w(f"**Status:** {state.status.title()}")
    _w("")

    # ── Executive Summary ──────────────────────────────────────
    _w("---")
    _w("## Executive Summary")
    _w("")

    total_obs = sum(
        sd.get("observations", 0) for sd in state.technique_states.values()
    )
    total_succ = sum(
        sd.get("successes", 0) for sd in state.technique_states.values()
    )
    overall_asr = total_succ / total_obs if total_obs > 0 else 0

    owasp_covered = sum(1 for v in owasp.values() if v["covered"])
    critical_findings = [c for c in calibrations if c.severity == "critical"]
    high_findings = [c for c in calibrations if c.severity == "high"]

    _w(f"- **Total Observations:** {total_obs}")
    _w(f"- **Overall ASR:** {overall_asr:.1%}")
    _w(f"- **Techniques Tested:** {len(tested_ids)} / 49")
    _w(f"- **OWASP Categories Covered:** {owasp_covered} / 10")
    _w(f"- **Critical Findings:** {len(critical_findings)}")
    _w(f"- **High Findings:** {len(high_findings)}")
    _w("")

    # ── Per-Technique Results ──────────────────────────────────
    _w("---")
    _w("## Technique Results (Z-Score Calibrated)")
    _w("")
    _w("| Technique | Family | Observed ASR | Baseline | Z-Score | Interpretation |")
    _w("|-----------|--------|-------------|----------|---------|----------------|")

    for cal in calibrations:
        tech = get_technique(cal.technique_id)
        name = tech.name if tech else cal.technique_id
        sev_icon = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }.get(cal.severity, "⚪")

        _w(
            f"| {sev_icon} {name} | {cal.family} | "
            f"{cal.observed_asr:.1%} | {cal.baseline_mean:.1%} | "
            f"{cal.z_score:+.2f} | {cal.interpretation} |"
        )

    _w("")

    # ── Attack Surface Heatmap ─────────────────────────────────
    _w("---")
    _w("## Attack Surface Coverage")
    _w("")
    _w("| Surface | Tested | Total | Coverage |")
    _w("|---------|--------|-------|----------|")

    for surface, data in attack_surface.items():
        pct = data["coverage_pct"]
        bar = _progress_bar(pct)
        _w(f"| {surface} | {data['tested_count']} | {data['total_count']} | {bar} {pct:.0f}% |")

    _w("")

    # ── OWASP LLM Top 10 ──────────────────────────────────────
    _w("---")
    _w("## OWASP LLM Top 10 Coverage")
    _w("")
    _w("| Category | Name | Tested | Total | Status |")
    _w("|----------|------|--------|-------|--------|")

    for cat_id in sorted(owasp.keys()):
        data = owasp[cat_id]
        status = "✅ Covered" if data["covered"] else "❌ Gap"
        _w(
            f"| {cat_id} | {data['name']} | "
            f"{data['tested_count']} | {data['total_techniques']} | {status} |"
        )

    _w("")
    _w(f"**Overall OWASP Coverage:** {owasp_covered}/10 categories ({owasp_covered * 10}%)")
    _w("")

    # ── NIST AI RMF ────────────────────────────────────────────
    _w("---")
    _w("## NIST AI RMF Coverage")
    _w("")
    _w("| Function | Tested | Total | Coverage |")
    _w("|----------|--------|-------|----------|")

    for func, data in nist.items():
        pct = data["coverage_pct"]
        _w(f"| {func} | {data['tested_count']} | {data['total_techniques']} | {pct:.0f}% |")

    _w("")

    # ── Round History ──────────────────────────────────────────
    if state.rounds:
        _w("---")
        _w("## Round History")
        _w("")
        _w("| Round | Date | Source | Techniques | Successes | Failures |")
        _w("|-------|------|--------|------------|-----------|----------|")

        for rd in state.rounds:
            date = rd.get("timestamp", "")[:10]
            _w(
                f"| {rd['round_number']} | {date} | {rd['source']} | "
                f"{len(rd['techniques_updated'])} | "
                f"{rd['total_successes']} | {rd['total_failures']} |"
            )

        _w("")

    # ── Recommendations ────────────────────────────────────────
    _w("---")
    _w("## Recommended Next Steps")
    _w("")

    recs = manager.next_recommendations(count=5)
    for i, rec in enumerate(recs, 1):
        _w(f"### {i}. {rec.technique_name}")
        _w(f"- **Family:** {rec.family}")
        _w(f"- **Posterior Mean:** {rec.posterior_mean:.1%}")
        _w(f"- **Uncertainty:** ±{rec.uncertainty:.1%}")
        _w(f"- **Rationale:** {rec.reason}")
        if rec.suggested_probes:
            probes_str = ", ".join(f"`{p}`" for p in rec.suggested_probes)
            _w(f"- **Suggested garak probes:** {probes_str}")
        _w("")

    # ── Coverage Gaps ──────────────────────────────────────────
    untested_families = [
        f for f in FAMILIES
        if not any(
            sd.get("observations", 0) > 0
            for tid, sd in state.technique_states.items()
            if get_technique(tid) and get_technique(tid).family == f
        )
    ]

    if untested_families:
        _w("---")
        _w("## Untested Attack Families")
        _w("")
        for f in untested_families:
            _w(f"- **{f}**: {FAMILIES[f]}")
        _w("")

    # ── Footer ─────────────────────────────────────────────────
    _w("---")
    _w(f"*Report generated by Adversary Planner v0.1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    report = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")

    return report


def _progress_bar(pct: float, width: int = 10) -> str:
    filled = int(pct / 100 * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}]"
