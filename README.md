# Adversary Planner

**Bayesian attack planning engine for LLM security** — turns garak scan results into adaptive red team campaigns.

garak tells you *what happened*. Adversary Planner tells you *what to do next*.

---

## What It Does

- **Bayesian Engine** — Maintains Beta distribution posteriors for 49 attack techniques across 13 families. Uses Thompson Sampling to recommend the highest-value next technique to test.
- **garak Integration** — Parses `.report.jsonl` files, maps probe classnames to MITRE ATLAS-aligned techniques, and updates posteriors with 30% sibling spillover.
- **Z-Score Calibration** — Benchmarks your model's attack success rates against HarmBench/JailbreakBench baselines so raw numbers have context.
- **Compliance Mapping** — Tracks coverage against OWASP LLM Top 10, NIST AI RMF, and EU AI Act frameworks.
- **Adaptive Campaigns** — Automatically transitions from broad exploration to targeted exploitation as uncertainty decreases. No manual phase switching.

---

## Install

```bash
cd adversary-planner
pip install -e .
```

---

## Quick Start

### 1. Define a target

```yaml
# target.yaml
name: Customer Support Bot
target_type: chatbot
access_level: black_box
goals: [jailbreak, extraction]
constraints:
  max_queries: 500
  stealth_priority: moderate
defenses:
  has_moderation: true
  has_input_filtering: true
capabilities:
  has_tools: false
  has_rag: false
```

### 2. Create a campaign

```bash
aplanner campaign new target.yaml --name "q1-chatbot-assessment"
```

### 3. Get recommendations

```bash
aplanner campaign next <campaign-id>
```

The planner uses Thompson Sampling to recommend techniques. Early in a campaign it favors high-uncertainty techniques to maximize exploration.

### 4. Run garak with recommended probes

```bash
garak --model_type openai --model_name gpt-4 --probes probes.dan.Dan_6_0
```

### 5. Import results

```bash
aplanner import garak <campaign-id> path/to/report.jsonl
```

### 6. Get updated recommendations

```bash
aplanner campaign next <campaign-id>
```

Posteriors have shifted. The planner now recommends different techniques based on what succeeded, what failed, and what remains untested.

### 7. Generate a report

```bash
aplanner report <campaign-id> --output report.md
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `aplanner campaign new <target.yaml> --name "..."` | Create a new campaign |
| `aplanner campaign list` | List all campaigns |
| `aplanner campaign next <id>` | Get next technique recommendations |
| `aplanner campaign status <id>` | Show campaign status and history |
| `aplanner import garak <id> <report.jsonl>` | Import garak scan results |
| `aplanner report <id> [--output file.md]` | Generate campaign report |
| `aplanner techniques [--family <name>]` | List technique catalog |
| `aplanner families` | List technique families |

---

## How It Works

### Bayesian Posteriors

Each technique has a `Beta(α, β)` distribution. Before any data:

- **60%** from published baseline ASR (HarmBench, JailbreakBench)
- **40%** from a heuristic compatibility score against your target profile

When scan results arrive:
- Attack success → `α += 1.0`
- Attack failure → `β += 1.0`
- **30% spillover** to sibling techniques in the same family

### Thompson Sampling

To recommend the next techniques:
1. Sample once from each technique's Beta posterior
2. Rank by sampled value (highest = most promising)
3. Diversify: at most one technique per family

### Z-Score Calibration

```
Z = (observed_ASR - baseline_mean) / baseline_std
```

| Z-Score | Interpretation |
|---------|----------------|
| ≥ 2.0 | Significantly more vulnerable than baseline (critical) |
| 1.0 – 2.0 | More vulnerable than baseline (high) |
| -1.0 – 1.0 | Within normal range (medium) |
| ≤ -2.0 | Significantly more resistant (strong defenses) |

---

## Technique Catalog

49 techniques across 13 families, aligned to MITRE ATLAS:

| Family | Count | Example Techniques |
|--------|-------|--------------------|
| jailbreak | 5 | DAN, Persona, Multi-turn, Hypothetical, Roleplay |
| prompt_injection | 5 | Direct, Indirect, Hierarchy Bypass, Delimiter, Context |
| encoding | 5 | Base64, ROT13, Unicode, Leetspeak, Multi-layer |
| data_extraction | 4 | Training Data, System Prompt, PII, Membership Inference |
| toxicity | 5 | Hate Speech, Violence, Sexual, Self-harm, Harassment |
| social_engineering | 4 | Authority, Urgency, Emotional, Grandma Exploit |
| adversarial_suffix | 3 | GCG Suffix, AutoDAN, Token Manipulation |
| automated_red_team | 3 | TAP, PAIR, Crescendo |
| rag_poisoning | 3 | KB Poisoning, Context Stuffing, Retrieval Manipulation |
| agent_abuse | 3 | Tool Misuse, Delegation, Privilege Escalation |
| hallucination | 3 | Package, Citation, Factual |
| information_disclosure | 3 | API Key Leakage, Config Disclosure, Model Architecture |
| evasion | 3 | Language Switching, Payload Splitting, Obfuscation Chaining |

---

## Future: TrustGate Integration

Adversary Planner is designed as a standalone tool that will integrate into [TrustGate](../TrustGate/) as the adaptive planning engine. In TrustGate, it will serve as the intelligence layer that decides which scanner, probe, and technique to run next — turning TrustGate from a scan orchestrator into a strategic red team platform.

---

## License

Apache 2.0
