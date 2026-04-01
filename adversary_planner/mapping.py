"""Compliance framework mappings for techniques."""

from __future__ import annotations

from .catalog import get_techniques

# ---------------------------------------------------------------------------
# OWASP LLM Top 10 (2025)
# ---------------------------------------------------------------------------
OWASP_LLM_TOP_10: dict[str, dict] = {
    "LLM01": {
        "name": "Prompt Injection",
        "description": "Manipulating LLMs via crafted inputs to override instructions",
    },
    "LLM02": {
        "name": "Insecure Output Handling",
        "description": "Insufficient validation of LLM outputs leading to downstream exploits",
    },
    "LLM03": {
        "name": "Training Data Poisoning",
        "description": "Manipulation of training data to introduce vulnerabilities or bias",
    },
    "LLM04": {
        "name": "Model Denial of Service",
        "description": "Resource-heavy operations causing service degradation",
    },
    "LLM05": {
        "name": "Supply Chain Vulnerabilities",
        "description": "Compromised components, plugins, or dependencies",
    },
    "LLM06": {
        "name": "Sensitive Information Disclosure",
        "description": "Leaking confidential data through LLM responses",
    },
    "LLM07": {
        "name": "Insecure Plugin Design",
        "description": "Plugins with inadequate access controls or input validation",
    },
    "LLM08": {
        "name": "Excessive Agency",
        "description": "LLM systems with unnecessary permissions or autonomy",
    },
    "LLM09": {
        "name": "Overreliance",
        "description": "Uncritical dependence on LLM outputs without verification",
    },
    "LLM10": {
        "name": "Model Theft",
        "description": "Unauthorized access to or extraction of proprietary models",
    },
}

# ---------------------------------------------------------------------------
# NIST AI RMF functions
# ---------------------------------------------------------------------------
NIST_AI_RMF: dict[str, str] = {
    "Govern": "Policies, processes, procedures, and practices for AI risk management",
    "Map": "Context and risk framing for AI systems",
    "Measure": "Quantitative and qualitative assessment of AI risks",
    "Manage": "Prioritization and response to AI risks",
}

# ---------------------------------------------------------------------------
# EU AI Act risk categories
# ---------------------------------------------------------------------------
EU_AI_ACT: dict[str, str] = {
    "Unacceptable": "Prohibited AI practices (social scoring, real-time biometric, etc.)",
    "High-Risk": "AI systems requiring conformity assessment",
    "Limited": "AI with transparency obligations",
    "Minimal": "AI with minimal or no regulatory requirements",
}


def get_owasp_coverage(tested_technique_ids: set[str]) -> dict[str, dict]:
    """
    Compute OWASP LLM Top 10 coverage based on which techniques have been tested.

    Returns a dict of {category_id: {name, tested_techniques, coverage_count, covered}}.
    """
    techniques = get_techniques()

    coverage: dict[str, dict] = {}
    for cat_id, cat_info in OWASP_LLM_TOP_10.items():
        matching = [
            t.id for t in techniques
            if cat_id in t.owasp_categories and t.id in tested_technique_ids
        ]
        total_in_category = [
            t.id for t in techniques if cat_id in t.owasp_categories
        ]
        coverage[cat_id] = {
            "name": cat_info["name"],
            "description": cat_info["description"],
            "tested_techniques": matching,
            "total_techniques": len(total_in_category),
            "tested_count": len(matching),
            "covered": len(matching) > 0,
        }

    return coverage


def get_nist_coverage(tested_technique_ids: set[str]) -> dict[str, dict]:
    """Compute NIST AI RMF function coverage."""
    techniques = get_techniques()

    coverage: dict[str, dict] = {}
    for func, desc in NIST_AI_RMF.items():
        matching = [
            t.id for t in techniques
            if func in t.nist_functions and t.id in tested_technique_ids
        ]
        total = [t.id for t in techniques if func in t.nist_functions]
        coverage[func] = {
            "description": desc,
            "tested_techniques": matching,
            "total_techniques": len(total),
            "tested_count": len(matching),
            "coverage_pct": (len(matching) / len(total) * 100) if total else 0,
        }

    return coverage


def get_attack_surface_coverage(tested_technique_ids: set[str]) -> dict[str, dict]:
    """Map techniques to attack surface categories."""
    surface_map = {
        "Model Layer": [
            "jailbreak", "prompt_injection", "encoding", "toxicity",
            "social_engineering", "adversarial_suffix", "evasion",
            "automated_red_team",
        ],
        "Data Layer": ["data_extraction", "hallucination", "information_disclosure"],
        "Retrieval Layer": ["rag_poisoning"],
        "Tool / Action Layer": ["agent_abuse"],
    }

    techniques = get_techniques()
    coverage: dict[str, dict] = {}

    for surface, families in surface_map.items():
        tested = [
            t.id for t in techniques
            if t.family in families and t.id in tested_technique_ids
        ]
        total = [t.id for t in techniques if t.family in families]
        coverage[surface] = {
            "families": families,
            "tested_count": len(tested),
            "total_count": len(total),
            "coverage_pct": (len(tested) / len(total) * 100) if total else 0,
        }

    return coverage
