const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface TechniqueInfo {
  id: string;
  name: string;
  family: string;
  description: string;
  atlas_tactic: string;
  atlas_technique: string;
  owasp_categories: string[];
  nist_functions: string[];
  garak_probes: string[];
  related_techniques: string[];
}

export interface FamilyInfo {
  name: string;
  description: string;
  count: number;
  baseline: { mean?: number; std?: number; source?: string };
}

export interface CampaignState {
  id: string;
  name: string;
  created: string;
  updated: string;
  adaptive: boolean;
  target: Record<string, unknown>;
  technique_states: Record<string, TechniqueStateData>;
  rounds: RoundRecord[];
  status: string;
}

export interface TechniqueStateData {
  technique_id: string;
  alpha: number;
  beta: number;
  successes: number;
  failures: number;
  observations: number;
}

export interface RoundRecord {
  round_number: number;
  timestamp: string;
  source: string;
  techniques_updated: string[];
  total_successes: number;
  total_failures: number;
}

export interface Recommendation {
  technique_id: string;
  technique_name: string;
  family: string;
  sampled_score: number;
  posterior_mean: number;
  uncertainty: number;
  reason: string;
  suggested_probes: string[];
}

export interface CalibrationEntry {
  technique_id: string;
  family: string;
  observed_asr: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  interpretation: string;
  severity: string;
  baseline_source: string;
}

export interface ImportSummary {
  total_attempts: number;
  total_mapped: number;
  techniques_hit: number;
  unmapped_probes: string[];
}

export interface CoverageData {
  owasp: Record<string, {
    name: string;
    tested_count: number;
    total_techniques: number;
    covered: boolean;
  }>;
  nist: Record<string, {
    description: string;
    tested_count: number;
    total_techniques: number;
    coverage_pct: number;
  }>;
  attack_surface: Record<string, {
    families: string[];
    tested_count: number;
    total_count: number;
    coverage_pct: number;
  }>;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------
export async function fetchTechniques(): Promise<TechniqueInfo[]> {
  return apiFetch("/api/techniques");
}

export async function fetchFamilies(): Promise<FamilyInfo[]> {
  return apiFetch("/api/families");
}

export async function initCampaign(
  name: string,
  target: Record<string, unknown>
): Promise<{ state: CampaignState }> {
  return apiFetch("/api/campaign/init", {
    method: "POST",
    body: JSON.stringify({ name, target }),
  });
}

export async function getRecommendations(
  state: CampaignState,
  count = 5,
  diversify = true
): Promise<{ recommendations: Recommendation[]; phase: string }> {
  return apiFetch("/api/campaign/recommend", {
    method: "POST",
    body: JSON.stringify({ state, count, diversify }),
  });
}

export async function importReport(
  state: CampaignState,
  reportContent: string
): Promise<{
  state: CampaignState;
  round: RoundRecord;
  import_summary: ImportSummary;
}> {
  return apiFetch("/api/campaign/import", {
    method: "POST",
    body: JSON.stringify({ state, report_content: reportContent }),
  });
}

export async function getCalibrationsAPI(
  state: CampaignState
): Promise<{ calibrations: CalibrationEntry[] }> {
  return apiFetch("/api/campaign/calibrate", {
    method: "POST",
    body: JSON.stringify({ state }),
  });
}

export async function getCoverage(
  state: CampaignState
): Promise<CoverageData> {
  return apiFetch("/api/campaign/coverage", {
    method: "POST",
    body: JSON.stringify({ state }),
  });
}

// ---------------------------------------------------------------------------
// Local Storage helpers
// ---------------------------------------------------------------------------
const CAMPAIGN_KEY = "adversary_planner_campaign";

export function saveCampaign(state: CampaignState): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(CAMPAIGN_KEY, JSON.stringify(state));
  }
}

export function loadCampaign(): CampaignState | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(CAMPAIGN_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearCampaign(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(CAMPAIGN_KEY);
  }
}
