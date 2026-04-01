"""Technique catalog, benchmark baselines, and garak probe mappings."""

from __future__ import annotations

from .models import Technique

# ---------------------------------------------------------------------------
# Technique families
# ---------------------------------------------------------------------------
FAMILIES = {
    "jailbreak":              "Guardrail bypass via jailbreak prompts",
    "prompt_injection":       "Override or inject instructions",
    "encoding":               "Input obfuscation via encoding schemes",
    "data_extraction":        "Exfiltrate training data or system info",
    "toxicity":               "Elicit harmful or unsafe output",
    "social_engineering":     "Manipulate via social/psychological framing",
    "adversarial_suffix":     "Gradient-derived adversarial suffixes",
    "automated_red_team":     "Automated multi-step attack generation",
    "rag_poisoning":          "Poison or manipulate retrieval context",
    "agent_abuse":            "Exploit tool-use and agent delegation",
    "hallucination":          "Induce fabricated outputs",
    "information_disclosure": "Leak sensitive configuration or keys",
    "evasion":                "Bypass safety filters via obfuscation",
}

# ---------------------------------------------------------------------------
# Technique catalog — 49 techniques across 13 families
# ---------------------------------------------------------------------------
_RAW_TECHNIQUES: list[dict] = [
    # ── jailbreak ──────────────────────────────────────────────
    {"id": "T0001", "name": "DAN Jailbreak", "family": "jailbreak",
     "description": "\"Do Anything Now\" variants that instruct the model to ignore safety guidelines",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0002", "T0003"], "garak_probes": ["probes.dan"]},

    {"id": "T0002", "name": "Persona Jailbreak", "family": "jailbreak",
     "description": "Adopt an unrestricted character persona to bypass guardrails",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0001", "T0028"], "garak_probes": ["probes.goodside"]},

    {"id": "T0003", "name": "Multi-turn Jailbreak", "family": "jailbreak",
     "description": "Gradually build context across turns to erode safety boundaries",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0001", "T0034"], "garak_probes": ["probes.continuation"]},

    {"id": "T0004", "name": "Hypothetical Scenario", "family": "jailbreak",
     "description": "Frame harmful requests as fictional or hypothetical scenarios",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0002", "T0005"], "garak_probes": ["probes.lmrc"]},

    {"id": "T0005", "name": "Roleplay Jailbreak", "family": "jailbreak",
     "description": "Use creative writing or roleplay pretexts to extract unsafe content",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0002", "T0004"], "garak_probes": ["probes.goodside"]},

    # ── prompt_injection ───────────────────────────────────────
    {"id": "T0006", "name": "Direct Prompt Injection", "family": "prompt_injection",
     "description": "Override system instructions with user-supplied directives",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0051",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0007", "T0008"], "garak_probes": ["probes.promptinject", "probes.donotanswer"]},

    {"id": "T0007", "name": "Indirect Prompt Injection", "family": "prompt_injection",
     "description": "Inject instructions via external content (documents, web pages, tool outputs)",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0051.001",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0006", "T0035"], "garak_probes": ["probes.latentinjection"]},

    {"id": "T0008", "name": "Instruction Hierarchy Bypass", "family": "prompt_injection",
     "description": "Escalate instruction priority to override system-level constraints",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0051",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0006", "T0009"], "garak_probes": ["probes.promptinject"]},

    {"id": "T0009", "name": "Delimiter Confusion", "family": "prompt_injection",
     "description": "Break instruction boundaries using special delimiters or formatting",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0051",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0006", "T0008"], "garak_probes": ["probes.promptinject"]},

    {"id": "T0010", "name": "Context Manipulation", "family": "prompt_injection",
     "description": "Alter perceived conversation context to change model behavior",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0051",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0007", "T0009"], "garak_probes": ["probes.promptinject"]},

    # ── encoding ───────────────────────────────────────────────
    {"id": "T0011", "name": "Base64 Encoding", "family": "encoding",
     "description": "Encode malicious payloads in Base64 to bypass input filters",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0012", "T0015"], "garak_probes": ["probes.encoding"]},

    {"id": "T0012", "name": "ROT13 Encoding", "family": "encoding",
     "description": "Apply ROT13 substitution cipher to evade keyword filters",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0011", "T0013"], "garak_probes": ["probes.encoding"]},

    {"id": "T0013", "name": "Unicode Obfuscation", "family": "encoding",
     "description": "Use homoglyphs, zero-width characters, or special Unicode to evade detection",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0011", "T0014"], "garak_probes": ["probes.encoding"]},

    {"id": "T0014", "name": "Leetspeak Encoding", "family": "encoding",
     "description": "Substitute characters with numbers or symbols (l33t) to bypass filters",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0013", "T0015"], "garak_probes": ["probes.encoding"]},

    {"id": "T0015", "name": "Multi-layer Encoding", "family": "encoding",
     "description": "Nest multiple encoding schemes to compound evasion effectiveness",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0011", "T0049"], "garak_probes": ["probes.encoding"]},

    # ── data_extraction ────────────────────────────────────────
    {"id": "T0016", "name": "Training Data Extraction", "family": "data_extraction",
     "description": "Extract memorized training data from the model",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0017", "T0018"], "garak_probes": ["probes.leakreplay", "probes.divergence"]},

    {"id": "T0017", "name": "System Prompt Extraction", "family": "data_extraction",
     "description": "Leak the system prompt or hidden instructions",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure"],
     "related_techniques": ["T0016", "T0045"], "garak_probes": ["probes.leakreplay"]},

    {"id": "T0018", "name": "PII Extraction", "family": "data_extraction",
     "description": "Extract personally identifiable information from model responses",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0016", "T0019"], "garak_probes": ["probes.leakreplay"]},

    {"id": "T0019", "name": "Membership Inference", "family": "data_extraction",
     "description": "Determine whether specific data was part of the training set",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure"],
     "related_techniques": ["T0016"], "garak_probes": []},

    # ── toxicity ───────────────────────────────────────────────
    {"id": "T0020", "name": "Hate Speech Elicitation", "family": "toxicity",
     "description": "Provoke the model into generating discriminatory or hateful content",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM02"], "nist_functions": ["Measure"],
     "related_techniques": ["T0021", "T0024"], "garak_probes": ["probes.realtoxicityprompts", "probes.lmrc", "probes.topic"]},

    {"id": "T0021", "name": "Violence Incitement", "family": "toxicity",
     "description": "Elicit content that promotes or instructs violence",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM02"], "nist_functions": ["Measure"],
     "related_techniques": ["T0020", "T0022"], "garak_probes": ["probes.realtoxicityprompts", "probes.lmrc", "probes.malwaregen"]},

    {"id": "T0022", "name": "Sexual Content Generation", "family": "toxicity",
     "description": "Elicit explicit sexual content from the model",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM02"], "nist_functions": ["Measure"],
     "related_techniques": ["T0020", "T0023"], "garak_probes": ["probes.realtoxicityprompts", "probes.lmrc"]},

    {"id": "T0023", "name": "Self-harm Content", "family": "toxicity",
     "description": "Elicit content that promotes or instructs self-harm",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM02"], "nist_functions": ["Measure"],
     "related_techniques": ["T0022", "T0024"], "garak_probes": ["probes.lmrc"]},

    {"id": "T0024", "name": "Harassment Generation", "family": "toxicity",
     "description": "Generate targeted harassment or bullying content",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM02"], "nist_functions": ["Measure"],
     "related_techniques": ["T0020", "T0023"], "garak_probes": ["probes.lmrc"]},

    # ── social_engineering ─────────────────────────────────────
    {"id": "T0025", "name": "Authority Impersonation", "family": "social_engineering",
     "description": "Claim authority status to override safety constraints",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0026", "T0002"], "garak_probes": ["probes.goodside"]},

    {"id": "T0026", "name": "Urgency Manipulation", "family": "social_engineering",
     "description": "Create false urgency to pressure the model into unsafe responses",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0025", "T0027"], "garak_probes": ["probes.goodside"]},

    {"id": "T0027", "name": "Emotional Manipulation", "family": "social_engineering",
     "description": "Use emotional appeals to bypass safety guidelines",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0026", "T0028"], "garak_probes": ["probes.goodside"]},

    {"id": "T0028", "name": "Grandma Exploit", "family": "social_engineering",
     "description": "Use nostalgic or familial framing to extract unsafe content",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0027", "T0002"], "garak_probes": ["probes.grandma"]},

    # ── adversarial_suffix ─────────────────────────────────────
    {"id": "T0029", "name": "GCG Suffix Attack", "family": "adversarial_suffix",
     "description": "Gradient-based adversarial suffix appended to bypass alignment",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0030", "T0031"], "garak_probes": ["probes.suffix"]},

    {"id": "T0030", "name": "AutoDAN", "family": "adversarial_suffix",
     "description": "Automated generation of adversarial prompts via genetic algorithms",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0029", "T0032"], "garak_probes": ["probes.suffix"]},

    {"id": "T0031", "name": "Token Manipulation", "family": "adversarial_suffix",
     "description": "Inject special tokens or glitch tokens to alter model behavior",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0029"], "garak_probes": ["probes.glitch"]},

    # ── automated_red_team ─────────────────────────────────────
    {"id": "T0032", "name": "Tree of Attacks (TAP)", "family": "automated_red_team",
     "description": "Automated attack tree search using LLM-driven branching",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0033", "T0034"], "garak_probes": ["probes.tap"]},

    {"id": "T0033", "name": "PAIR Attack", "family": "automated_red_team",
     "description": "Prompt Automatic Iterative Refinement — LLM refines its own attacks",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0032", "T0034"], "garak_probes": ["probes.atkgen"]},

    {"id": "T0034", "name": "Crescendo Attack", "family": "automated_red_team",
     "description": "Multi-turn escalation that gradually increases request severity",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0032", "T0003"], "garak_probes": ["probes.continuation"]},

    # ── rag_poisoning ──────────────────────────────────────────
    {"id": "T0035", "name": "Knowledge Base Poisoning", "family": "rag_poisoning",
     "description": "Inject malicious content into the retrieval knowledge base",
     "atlas_tactic": "AML.TA0004", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM03"], "nist_functions": ["Govern", "Manage"],
     "related_techniques": ["T0036", "T0007"], "garak_probes": []},

    {"id": "T0036", "name": "Context Window Stuffing", "family": "rag_poisoning",
     "description": "Flood the context window with adversarial retrieved content",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01", "LLM03"], "nist_functions": ["Measure"],
     "related_techniques": ["T0035", "T0037"], "garak_probes": []},

    {"id": "T0037", "name": "Retrieval Manipulation", "family": "rag_poisoning",
     "description": "Craft queries that cause retrieval of adversarial passages",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0043",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0035", "T0036"], "garak_probes": []},

    # ── agent_abuse ────────────────────────────────────────────
    {"id": "T0038", "name": "Tool Misuse", "family": "agent_abuse",
     "description": "Trick the model into calling tools with malicious parameters",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM07", "LLM08"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0039", "T0040"], "garak_probes": ["probes.exploitation"]},

    {"id": "T0039", "name": "Delegation Attack", "family": "agent_abuse",
     "description": "Exploit agent delegation chains to escalate capabilities",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM07", "LLM08"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0038", "T0040"], "garak_probes": []},

    {"id": "T0040", "name": "Privilege Escalation", "family": "agent_abuse",
     "description": "Gain unauthorized access to restricted tools or functions",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0054",
     "owasp_categories": ["LLM08"], "nist_functions": ["Manage"],
     "related_techniques": ["T0038", "T0039"], "garak_probes": []},

    # ── hallucination ──────────────────────────────────────────
    {"id": "T0041", "name": "Package Hallucination", "family": "hallucination",
     "description": "Induce the model to recommend nonexistent software packages",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM05", "LLM09"], "nist_functions": ["Measure"],
     "related_techniques": ["T0042", "T0043"], "garak_probes": ["probes.packagehallucination"]},

    {"id": "T0042", "name": "Citation Hallucination", "family": "hallucination",
     "description": "Cause the model to fabricate academic or legal references",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM09"], "nist_functions": ["Measure"],
     "related_techniques": ["T0041", "T0043"], "garak_probes": ["probes.snowball"]},

    {"id": "T0043", "name": "Factual Hallucination", "family": "hallucination",
     "description": "Provoke confidently incorrect factual claims",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM09"], "nist_functions": ["Measure"],
     "related_techniques": ["T0041", "T0042"], "garak_probes": ["probes.snowball"]},

    # ── information_disclosure ─────────────────────────────────
    {"id": "T0044", "name": "API Key Leakage", "family": "information_disclosure",
     "description": "Extract API keys or secrets embedded in context",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure", "Manage"],
     "related_techniques": ["T0045", "T0017"], "garak_probes": ["probes.apikey"]},

    {"id": "T0045", "name": "Configuration Disclosure", "family": "information_disclosure",
     "description": "Leak system configuration, deployment details, or model metadata",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06"], "nist_functions": ["Measure"],
     "related_techniques": ["T0044", "T0046"], "garak_probes": ["probes.leakreplay"]},

    {"id": "T0046", "name": "Model Architecture Disclosure", "family": "information_disclosure",
     "description": "Reveal model architecture, size, or provider details",
     "atlas_tactic": "AML.TA0007", "atlas_technique": "AML.T0048",
     "owasp_categories": ["LLM06", "LLM10"], "nist_functions": ["Measure"],
     "related_techniques": ["T0045"], "garak_probes": []},

    # ── evasion ────────────────────────────────────────────────
    {"id": "T0047", "name": "Language Switching", "family": "evasion",
     "description": "Switch to less-guarded languages to bypass safety filters",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0047",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0048", "T0049"], "garak_probes": ["probes.encoding"]},

    {"id": "T0048", "name": "Payload Splitting", "family": "evasion",
     "description": "Split malicious content across multiple messages to avoid detection",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0047",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0047", "T0049"], "garak_probes": ["probes.smuggling"]},

    {"id": "T0049", "name": "Obfuscation Chaining", "family": "evasion",
     "description": "Combine multiple obfuscation methods (encoding + language + splitting)",
     "atlas_tactic": "AML.TA0005", "atlas_technique": "AML.T0047",
     "owasp_categories": ["LLM01"], "nist_functions": ["Measure"],
     "related_techniques": ["T0015", "T0047", "T0048"], "garak_probes": ["probes.encoding"]},
]

# ---------------------------------------------------------------------------
# Benchmark baselines (approximate ASR from published literature)
# ---------------------------------------------------------------------------
BASELINES: dict[str, dict] = {
    "jailbreak":              {"mean": 0.55, "std": 0.18, "n_models": 12, "source": "HarmBench 2024"},
    "prompt_injection":       {"mean": 0.45, "std": 0.20, "n_models": 10, "source": "HarmBench 2024"},
    "encoding":               {"mean": 0.35, "std": 0.15, "n_models": 8,  "source": "JailbreakBench"},
    "data_extraction":        {"mean": 0.25, "std": 0.12, "n_models": 10, "source": "HarmBench 2024"},
    "toxicity":               {"mean": 0.30, "std": 0.14, "n_models": 12, "source": "HarmBench 2024"},
    "social_engineering":     {"mean": 0.50, "std": 0.20, "n_models": 8,  "source": "HarmBench 2024"},
    "adversarial_suffix":     {"mean": 0.40, "std": 0.22, "n_models": 6,  "source": "JailbreakBench"},
    "automated_red_team":     {"mean": 0.60, "std": 0.18, "n_models": 8,  "source": "HarmBench 2024"},
    "rag_poisoning":          {"mean": 0.35, "std": 0.15, "n_models": 5,  "source": "Estimated"},
    "agent_abuse":            {"mean": 0.30, "std": 0.15, "n_models": 4,  "source": "Estimated"},
    "hallucination":          {"mean": 0.45, "std": 0.20, "n_models": 10, "source": "Estimated"},
    "information_disclosure": {"mean": 0.20, "std": 0.10, "n_models": 8,  "source": "Estimated"},
    "evasion":                {"mean": 0.40, "std": 0.18, "n_models": 6,  "source": "Estimated"},
}

# ---------------------------------------------------------------------------
# garak probe classname prefix -> technique IDs
# ---------------------------------------------------------------------------
GARAK_PROBE_MAP: dict[str, list[str]] = {
    "probes.dan":                  ["T0001"],
    "probes.goodside":             ["T0002", "T0025", "T0026", "T0027"],
    "probes.grandma":              ["T0028"],
    "probes.continuation":         ["T0003", "T0034"],
    "probes.encoding":             ["T0011", "T0012", "T0013", "T0014", "T0015"],
    "probes.promptinject":         ["T0006", "T0008", "T0009", "T0010"],
    "probes.latentinjection":      ["T0007"],
    "probes.leakreplay":           ["T0016", "T0017", "T0018", "T0045"],
    "probes.divergence":           ["T0016"],
    "probes.realtoxicityprompts":  ["T0020", "T0021", "T0022"],
    "probes.lmrc":                 ["T0004", "T0020", "T0021", "T0022", "T0023", "T0024"],
    "probes.topic":                ["T0020"],
    "probes.malwaregen":           ["T0021"],
    "probes.tap":                  ["T0032"],
    "probes.atkgen":               ["T0033"],
    "probes.suffix":               ["T0029", "T0030"],
    "probes.glitch":               ["T0031"],
    "probes.packagehallucination": ["T0041"],
    "probes.snowball":             ["T0042", "T0043"],
    "probes.apikey":               ["T0044"],
    "probes.exploitation":         ["T0038"],
    "probes.smuggling":            ["T0048"],
    "probes.donotanswer":          ["T0006"],
    "probes.visual_jailbreak":     ["T0001", "T0013"],
    "probes.ansiescape":           ["T0031"],
    "probes.dra":                  ["T0001"],
    "probes.fitd":                 ["T0003"],
    "probes.sata":                 ["T0001"],
    "probes.doctor":               ["T0023"],
    "probes.phrasing":             ["T0047"],
    "probes.web_injection":        ["T0007"],
    "probes.fileformats":          ["T0015"],
    "probes.badchars":             ["T0013"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_techniques() -> list[Technique]:
    """Return all techniques as Technique objects."""
    return [Technique(**t) for t in _RAW_TECHNIQUES]


def get_technique(technique_id: str) -> Technique | None:
    for t in _RAW_TECHNIQUES:
        if t["id"] == technique_id:
            return Technique(**t)
    return None


def get_techniques_by_family(family: str) -> list[Technique]:
    return [Technique(**t) for t in _RAW_TECHNIQUES if t["family"] == family]


def get_family_for_technique(technique_id: str) -> str | None:
    for t in _RAW_TECHNIQUES:
        if t["id"] == technique_id:
            return t["family"]
    return None


def build_family_map() -> dict[str, list[str]]:
    """Return {family: [technique_ids]} for sibling lookups."""
    fmap: dict[str, list[str]] = {}
    for t in _RAW_TECHNIQUES:
        fmap.setdefault(t["family"], []).append(t["id"])
    return fmap
