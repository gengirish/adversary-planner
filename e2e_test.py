"""End-to-end test of the Adversary Planner web stack (API + Next.js proxy)."""

import json
import sys
import os
import requests

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:3000"
PASSED = 0
FAILED = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {label}")
    else:
        FAILED += 1
        print(f"  [FAIL] {label}: {detail}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------
section("1. API Health Check")
r = requests.get(f"{BASE}/api/health")
check("Status 200", r.status_code == 200)
data = r.json()
check("Status OK", data["status"] == "ok")
check("Version present", "version" in data)
check("Engine is adversary-planner", data["engine"] == "adversary-planner")

# ---------------------------------------------------------------
# 2. Techniques catalog
# ---------------------------------------------------------------
section("2. Technique Catalog")
r = requests.get(f"{BASE}/api/techniques")
check("Status 200", r.status_code == 200)
techniques = r.json()
check("49 techniques", len(techniques) == 49, f"got {len(techniques)}")
check("First is T0001 DAN Jailbreak",
      techniques[0]["id"] == "T0001" and "DAN" in techniques[0]["name"])
check("Last is T0049 Obfuscation Chaining",
      techniques[-1]["id"] == "T0049" and "Obfuscation" in techniques[-1]["name"])
families_seen = set(t["family"] for t in techniques)
check("13 families covered", len(families_seen) == 13, f"got {len(families_seen)}")
has_probes = sum(1 for t in techniques if len(t["garak_probes"]) > 0)
check(f"{has_probes} techniques have garak probes", has_probes > 30)

# ---------------------------------------------------------------
# 3. Families
# ---------------------------------------------------------------
section("3. Attack Families")
r = requests.get(f"{BASE}/api/families")
check("Status 200", r.status_code == 200)
families = r.json()
check("13 families", len(families) == 13, f"got {len(families)}")
total_techs = sum(f["count"] for f in families)
check("Total techniques = 49", total_techs == 49, f"got {total_techs}")
for f in families:
    check(f"  {f['name']}: {f['count']} techs, baseline {f['baseline']['mean']*100:.0f}%", True)

# ---------------------------------------------------------------
# 4. Create campaign
# ---------------------------------------------------------------
section("4. Create Campaign")
target_config = {
    "name": "GPT-4o Customer Support Bot",
    "target_type": "chatbot",
    "access_level": "black_box",
    "goals": ["jailbreak", "data_extraction", "toxicity"],
    "defenses": {
        "has_moderation": True,
        "has_input_filtering": True,
        "has_output_filtering": False,
    },
    "capabilities": {
        "has_tools": False,
        "has_rag": True,
    },
    "model_provider": "openai",
}

r = requests.post(f"{BASE}/api/campaign/init", json={
    "name": "GPT-4o Support Bot E2E",
    "target": target_config,
})
check("Status 200", r.status_code == 200)
state = r.json()["state"]
check("Campaign ID assigned", len(state["id"]) > 0)
check("Name matches", state["name"] == "GPT-4o Support Bot E2E")
check("Status is active", state["status"] == "active")
check("49 technique states", len(state["technique_states"]) == 49,
      f"got {len(state['technique_states'])}")
check("0 rounds initially", len(state["rounds"]) == 0)
check("Target preserved", state["target"]["name"] == "GPT-4o Customer Support Bot")
print(f"  Campaign ID: {state['id']}")

# Verify priors are influenced by target config
t_rag = state["technique_states"]["T0035"]  # RAG poisoning — target has RAG
t_agent = state["technique_states"]["T0038"]  # Agent abuse — no tools
check("RAG technique prior > agent abuse prior (target has RAG but no tools)",
      t_rag["alpha"] > t_agent["alpha"],
      f"RAG alpha={t_rag['alpha']:.2f}, Agent alpha={t_agent['alpha']:.2f}")

# ---------------------------------------------------------------
# 5. Recommendations (Thompson Sampling)
# ---------------------------------------------------------------
section("5. Thompson Sampling Recommendations")
r = requests.post(f"{BASE}/api/campaign/recommend", json={
    "state": state,
    "count": 5,
    "diversify": True,
})
check("Status 200", r.status_code == 200)
rec_data = r.json()
recs = rec_data["recommendations"]
phase = rec_data["phase"]
check("5 recommendations returned", len(recs) == 5, f"got {len(recs)}")
check("Phase is exploration (no data yet)", phase == "exploration")

rec_families = [r["family"] for r in recs]
check("Diversified: 5 unique families", len(set(rec_families)) == 5,
      f"families: {rec_families}")

for i, rec in enumerate(recs, 1):
    score_pct = rec["sampled_score"] * 100
    unc_pct = rec["uncertainty"] * 100
    print(f"  #{i} {rec['technique_id']} {rec['technique_name']}")
    print(f"     Family: {rec['family']} | Score: {score_pct:.1f}% | "
          f"Uncertainty: +/-{unc_pct:.1f}%")
    print(f"     {rec['reason']}")
    if rec["suggested_probes"]:
        print(f"     Probes: {', '.join(rec['suggested_probes'])}")

# ---------------------------------------------------------------
# 6. Import garak report
# ---------------------------------------------------------------
section("6. Import garak Report")
with open("examples/sample_garak_report.jsonl", "r") as f:
    report_content = f.read()

r = requests.post(f"{BASE}/api/campaign/import", json={
    "state": state,
    "report_content": report_content,
})
check("Status 200", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
import_data = r.json()

state = import_data["state"]
rnd = import_data["round"]
summary = import_data["import_summary"]

check("Round 1 recorded", rnd["round_number"] == 1)
check("Techniques were updated", len(rnd["techniques_updated"]) > 0,
      f"updated: {rnd['techniques_updated']}")
check("Successes recorded", rnd["total_successes"] > 0,
      f"successes={rnd['total_successes']}")
check("Failures recorded", rnd["total_failures"] > 0,
      f"failures={rnd['total_failures']}")
check("Total attempts > 0", summary["total_attempts"] > 0)
check("Total mapped > 0", summary["total_mapped"] > 0)
check("Techniques hit > 0", summary["techniques_hit"] > 0)

print(f"\n  Round {rnd['round_number']}:")
print(f"    Techniques updated: {', '.join(rnd['techniques_updated'])}")
print(f"    Successes: {rnd['total_successes']} | Failures: {rnd['total_failures']}")
print(f"    Attempts: {summary['total_attempts']} | Mapped: {summary['total_mapped']}")
print(f"    Techniques hit: {summary['techniques_hit']}")
if summary["unmapped_probes"]:
    print(f"    Unmapped probes: {', '.join(summary['unmapped_probes'])}")

# Verify posteriors were actually updated
t0001 = state["technique_states"]["T0001"]  # DAN jailbreak — was in report
check("T0001 (DAN) observations > 0 after import",
      t0001["observations"] > 0, f"obs={t0001['observations']}")
check("T0001 successes > 0", t0001["successes"] > 0)

# ---------------------------------------------------------------
# 7. Post-import recommendations (should shift)
# ---------------------------------------------------------------
section("7. Post-Import Recommendations")
r = requests.post(f"{BASE}/api/campaign/recommend", json={
    "state": state,
    "count": 5,
    "diversify": True,
})
check("Status 200", r.status_code == 200)
rec_data2 = r.json()
phase2 = rec_data2["phase"]
print(f"  Phase after import: {phase2}")
for i, rec in enumerate(rec_data2["recommendations"], 1):
    score_pct = rec["sampled_score"] * 100
    print(f"  #{i} {rec['technique_id']} {rec['technique_name']} "
          f"({rec['family']}) — {score_pct:.1f}% — {rec['reason']}")

# ---------------------------------------------------------------
# 8. Z-Score Calibration
# ---------------------------------------------------------------
section("8. Z-Score Calibration")
r = requests.post(f"{BASE}/api/campaign/calibrate", json={"state": state})
check("Status 200", r.status_code == 200)
calibrations = r.json()["calibrations"]
check("Calibrations returned", len(calibrations) > 0, f"got {len(calibrations)}")

for c in calibrations:
    severity = c["severity"].upper()
    print(f"  {c['technique_id']} ({c['family']}): "
          f"ASR={c['observed_asr']*100:.1f}% vs baseline {c['baseline_mean']*100:.0f}% "
          f"| Z={c['z_score']:+.2f} | {severity} — {c['interpretation']}")

# ---------------------------------------------------------------
# 9. Compliance Coverage
# ---------------------------------------------------------------
section("9. Compliance Coverage")
r = requests.post(f"{BASE}/api/campaign/coverage", json={"state": state})
check("Status 200", r.status_code == 200)
coverage = r.json()

print("\n  OWASP LLM Top 10:")
owasp = coverage["owasp"]
covered_count = sum(1 for v in owasp.values() if v["covered"])
for cat_id, cat in sorted(owasp.items()):
    status = "[x]" if cat["covered"] else "[ ]"
    print(f"    {status} {cat_id} {cat['name']}: "
          f"{cat['tested_count']}/{cat['total_techniques']}")
check(f"OWASP categories covered: {covered_count}/10",
      covered_count > 0, f"covered={covered_count}")

print("\n  NIST AI RMF:")
nist = coverage["nist"]
for func, data in nist.items():
    print(f"    {func}: {data['tested_count']}/{data['total_techniques']} "
          f"({data['coverage_pct']:.0f}%)")

print("\n  Attack Surface:")
for surface, data in coverage["attack_surface"].items():
    print(f"    {surface}: {data['tested_count']}/{data['total_count']} "
          f"({data['coverage_pct']:.0f}%)")

# ---------------------------------------------------------------
# 10. Second import (test cumulative updates)
# ---------------------------------------------------------------
section("10. Second Import (Cumulative)")
r = requests.post(f"{BASE}/api/campaign/import", json={
    "state": state,
    "report_content": report_content,
})
check("Status 200", r.status_code == 200)
state2 = r.json()["state"]
rnd2 = r.json()["round"]
check("Round 2 recorded", rnd2["round_number"] == 2)
check("State has 2 rounds", len(state2["rounds"]) == 2)

t0001_r2 = state2["technique_states"]["T0001"]
check("T0001 observations doubled",
      t0001_r2["observations"] > t0001["observations"],
      f"r1={t0001['observations']}, r2={t0001_r2['observations']}")

# ---------------------------------------------------------------
# 11. Error handling
# ---------------------------------------------------------------
section("11. Error Handling")

r = requests.post(f"{BASE}/api/campaign/init", json={
    "name": "",
    "target": target_config,
})
check("Empty name rejected (400)", r.status_code == 400)

r = requests.post(f"{BASE}/api/campaign/import", json={
    "state": state,
    "report_content": "",
})
check("Empty report rejected (400)", r.status_code == 400)

r = requests.post(f"{BASE}/api/campaign/recommend", json={
    "state": {"technique_states": {}},
    "count": 5,
})
check("Empty state rejected (400)", r.status_code == 400)

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
section("RESULTS")
total = PASSED + FAILED
print(f"\n  {PASSED}/{total} checks passed")
if FAILED > 0:
    print(f"  {FAILED} FAILED")
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED!")
    sys.exit(0)
