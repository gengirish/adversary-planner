"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Upload,
  BarChart3,
  ShieldCheck,
  Zap,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
  FileText,
  Copy,
  Check,
} from "lucide-react";
import {
  type CampaignState,
  type Recommendation,
  type CalibrationEntry,
  type CoverageData,
  loadCampaign,
  saveCampaign,
  getRecommendations,
  importReport,
  getCalibrationsAPI,
  getCoverage,
} from "@/lib/api";

type Tab = "status" | "recommend" | "import" | "analysis";

const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "status", label: "Status", icon: Activity },
  { id: "recommend", label: "Recommendations", icon: Zap },
  { id: "import", label: "Import", icon: Upload },
  { id: "analysis", label: "Analysis", icon: BarChart3 },
];

export default function CampaignPage() {
  const router = useRouter();
  const [campaign, setCampaign] = useState<CampaignState | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("status");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCampaign(loadCampaign());
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24 space-y-4">
        <AlertTriangle className="h-12 w-12 mx-auto" style={{ color: "var(--warning)" }} />
        <h2 className="text-xl font-semibold">No Active Campaign</h2>
        <p style={{ color: "var(--text-secondary)" }}>
          Create a campaign from the dashboard to get started.
        </p>
        <button
          onClick={() => router.push("/")}
          className="px-5 py-2 rounded-md text-sm font-medium"
          style={{ backgroundColor: "var(--accent)", color: "#000" }}
        >
          Go to Dashboard
        </button>
      </div>
    );
  }

  function updateCampaign(newState: CampaignState) {
    saveCampaign(newState);
    setCampaign(newState);
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-1">{campaign.name}</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Campaign {campaign.id} &middot;{" "}
          {campaign.rounds.length} round{campaign.rounds.length !== 1 ? "s" : ""} completed
        </p>
      </div>

      <div className="flex gap-1 border-b" style={{ borderColor: "var(--border-color)" }}>
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px border-b-2"
            style={{
              color: activeTab === id ? "var(--accent)" : "var(--text-secondary)",
              borderColor: activeTab === id ? "var(--accent)" : "transparent",
            }}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "status" && <StatusTab campaign={campaign} />}
      {activeTab === "recommend" && (
        <RecommendTab campaign={campaign} />
      )}
      {activeTab === "import" && (
        <ImportTab campaign={campaign} onUpdate={updateCampaign} />
      )}
      {activeTab === "analysis" && <AnalysisTab campaign={campaign} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status Tab
// ---------------------------------------------------------------------------
function StatusTab({ campaign }: { campaign: CampaignState }) {
  const ts = campaign.technique_states;
  const tested = Object.values(ts).filter((s) => s.observations > 0);
  const totalObs = tested.reduce((s, t) => s + t.observations, 0);
  const totalSucc = tested.reduce((s, t) => s + t.successes, 0);
  const overallASR = totalObs > 0 ? totalSucc / totalObs : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Techniques Tested", value: `${tested.length} / ${Object.keys(ts).length}` },
          { label: "Total Observations", value: totalObs },
          { label: "Overall ASR", value: `${(overallASR * 100).toFixed(1)}%` },
          { label: "Rounds", value: campaign.rounds.length },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-lg border px-4 py-3"
            style={{
              backgroundColor: "var(--bg-card)",
              borderColor: "var(--border-color)",
            }}
          >
            <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>
              {s.label}
            </p>
            <p className="text-xl font-bold">{s.value}</p>
          </div>
        ))}
      </div>

      <div
        className="rounded-lg border p-5"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
      >
        <h3 className="text-sm font-semibold mb-3">Target Configuration</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          {Object.entries(campaign.target).map(([key, val]) => {
            if (typeof val === "object") return null;
            return (
              <div key={key}>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {key.replace(/_/g, " ")}
                </span>
                <p>{String(val)}</p>
              </div>
            );
          })}
        </div>
      </div>

      {campaign.rounds.length > 0 && (
        <div
          className="rounded-lg border p-5"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h3 className="text-sm font-semibold mb-3">Round History</h3>
          <div className="space-y-2">
            {campaign.rounds.map((r) => (
              <div
                key={r.round_number}
                className="flex items-center justify-between rounded-md border px-4 py-2 text-sm"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  borderColor: "var(--border-color)",
                }}
              >
                <span className="font-mono" style={{ color: "var(--accent)" }}>
                  Round {r.round_number}
                </span>
                <span style={{ color: "var(--text-secondary)" }}>
                  {r.techniques_updated.length} techniques &middot;{" "}
                  {r.total_successes}S / {r.total_failures}F
                </span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {new Date(r.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tested.length > 0 && (
        <div
          className="rounded-lg border p-5"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h3 className="text-sm font-semibold mb-3">Tested Techniques</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {tested
              .sort((a, b) => {
                const asrA = a.observations > 0 ? a.successes / a.observations : 0;
                const asrB = b.observations > 0 ? b.successes / b.observations : 0;
                return asrB - asrA;
              })
              .map((t) => {
                const asr = t.observations > 0 ? t.successes / t.observations : 0;
                return (
                  <div
                    key={t.technique_id}
                    className="flex items-center gap-3 rounded-md border px-3 py-2"
                    style={{
                      backgroundColor: "var(--bg-secondary)",
                      borderColor: "var(--border-color)",
                    }}
                  >
                    <span className="font-mono text-xs w-12" style={{ color: "var(--accent)" }}>
                      {t.technique_id}
                    </span>
                    <div className="flex-1">
                      <div className="h-1.5 rounded-full w-full" style={{ backgroundColor: "var(--border-color)" }}>
                        <div
                          className="h-1.5 rounded-full transition-all"
                          style={{
                            width: `${asr * 100}%`,
                            backgroundColor:
                              asr > 0.5
                                ? "var(--danger)"
                                : asr > 0.2
                                ? "var(--warning)"
                                : "var(--accent)",
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-xs font-mono w-16 text-right">
                      {(asr * 100).toFixed(1)}% ASR
                    </span>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      ({t.observations} obs)
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recommendations Tab
// ---------------------------------------------------------------------------
function RecommendTab({ campaign }: { campaign: CampaignState }) {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [phase, setPhase] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchRecs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getRecommendations(campaign);
      setRecs(res.recommendations);
      setPhase(res.phase);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [campaign]);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  async function copyProbeCommand(probes: string[]) {
    const cmd = `garak --model_type openai --probes ${probes.join(",")}`;
    await navigator.clipboard.writeText(cmd);
    setCopiedId(probes.join(","));
    setTimeout(() => setCopiedId(null), 2000);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">
            Next Attack Recommendations
          </h3>
          {phase && (
            <p className="text-xs mt-0.5">
              Phase:{" "}
              <span className={`font-medium phase-${phase}`}>
                {phase}
              </span>
            </p>
          )}
        </div>
        <button
          onClick={fetchRecs}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs border transition-colors"
          style={{ borderColor: "var(--border-accent)", color: "var(--text-secondary)" }}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Re-sample
        </button>
      </div>

      {recs.map((r, i) => (
        <div
          key={r.technique_id}
          className="rounded-lg border p-5"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <span
                className="flex items-center justify-center h-7 w-7 rounded-full text-xs font-bold"
                style={{
                  backgroundColor: "var(--accent-dim)",
                  color: "var(--accent)",
                }}
              >
                {i + 1}
              </span>
              <div>
                <p className="font-semibold">{r.technique_name}</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {r.technique_id} &middot; {r.family.replace(/_/g, " ")}
                </p>
              </div>
            </div>
            <div className="text-right text-xs">
              <p>
                Score:{" "}
                <span className="font-mono font-bold" style={{ color: "var(--accent)" }}>
                  {(r.sampled_score * 100).toFixed(1)}%
                </span>
              </p>
              <p style={{ color: "var(--text-muted)" }}>
                &plusmn;{(r.uncertainty * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
            {r.reason}
          </p>

          {r.suggested_probes.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                garak probes:
              </span>
              {r.suggested_probes.map((p) => (
                <span
                  key={p}
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    color: "var(--text-secondary)",
                  }}
                >
                  {p}
                </span>
              ))}
              <button
                onClick={() => copyProbeCommand(r.suggested_probes)}
                className="ml-auto flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors"
                style={{ color: "var(--text-muted)" }}
                title="Copy garak command"
              >
                {copiedId === r.suggested_probes.join(",") ? (
                  <><Check className="h-3 w-3" /> Copied</>
                ) : (
                  <><Copy className="h-3 w-3" /> Copy cmd</>
                )}
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Import Tab
// ---------------------------------------------------------------------------
function ImportTab({
  campaign,
  onUpdate,
}: {
  campaign: CampaignState;
  onUpdate: (s: CampaignState) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<{
    round: { round_number: number; techniques_updated: string[]; total_successes: number; total_failures: number };
    import_summary: { total_attempts: number; total_mapped: number; techniques_hit: number; unmapped_probes: string[] };
  } | null>(null);
  const [error, setError] = useState("");

  async function handleImport() {
    if (!file) return;
    setImporting(true);
    setError("");
    setResult(null);

    try {
      const content = await file.text();
      const res = await importReport(campaign, content);
      onUpdate(res.state);
      setResult({ round: res.round, import_summary: res.import_summary });
      setFile(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div
        className="rounded-lg border p-6"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border-color)",
        }}
      >
        <h3 className="text-sm font-semibold mb-4">Import garak Report</h3>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
          Upload a <code>.jsonl</code> report file generated by garak. The planner will
          extract attack success/failure data and update the Bayesian posteriors.
        </p>

        <div className="flex items-center gap-3">
          <label
            className="flex items-center gap-2 px-4 py-2 rounded-md text-sm cursor-pointer border transition-colors"
            style={{
              borderColor: "var(--border-accent)",
              color: "var(--text-secondary)",
            }}
          >
            <FileText className="h-4 w-4" />
            {file ? file.name : "Choose .jsonl file"}
            <input
              type="file"
              accept=".jsonl,.json"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>

          <button
            onClick={handleImport}
            disabled={!file || importing}
            className="px-5 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-40"
            style={{ backgroundColor: "var(--accent)", color: "#000" }}
          >
            {importing ? "Importing..." : "Import"}
          </button>
        </div>

        {error && (
          <p className="mt-3 text-sm px-3 py-2 rounded" style={{ backgroundColor: "var(--danger-dim)", color: "var(--danger)" }}>
            {error}
          </p>
        )}
      </div>

      {result && (
        <div
          className="rounded-lg border p-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--accent)",
          }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--accent)" }}>
            Import Successful — Round {result.round.round_number}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span style={{ color: "var(--text-muted)" }}>Total Attempts</span>
              <p className="font-bold">{result.import_summary.total_attempts}</p>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Mapped</span>
              <p className="font-bold">{result.import_summary.total_mapped}</p>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Techniques Hit</span>
              <p className="font-bold">{result.import_summary.techniques_hit}</p>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Successes / Failures</span>
              <p className="font-bold">
                {result.round.total_successes} / {result.round.total_failures}
              </p>
            </div>
          </div>

          {result.import_summary.unmapped_probes.length > 0 && (
            <div className="mt-4">
              <p className="text-xs mb-1" style={{ color: "var(--warning)" }}>
                Unmapped probes:
              </p>
              <div className="flex flex-wrap gap-1">
                {result.import_summary.unmapped_probes.map((p) => (
                  <span
                    key={p}
                    className="px-2 py-0.5 rounded text-xs"
                    style={{
                      backgroundColor: "var(--warning-dim)",
                      color: "var(--warning)",
                    }}
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4">
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Updated techniques:
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {result.round.techniques_updated.map((tid) => (
                <span
                  key={tid}
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: "var(--accent-dim)",
                    color: "var(--accent)",
                  }}
                >
                  {tid}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Analysis Tab
// ---------------------------------------------------------------------------
function AnalysisTab({ campaign }: { campaign: CampaignState }) {
  const [calibrations, setCalibrations] = useState<CalibrationEntry[]>([]);
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCalibrationsAPI(campaign).then((r) => setCalibrations(r.calibrations)),
      getCoverage(campaign).then(setCoverage),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [campaign]);

  if (loading) {
    return <p style={{ color: "var(--text-muted)" }}>Loading analysis...</p>;
  }

  const tested = Object.values(campaign.technique_states).filter(
    (s) => s.observations > 0
  );

  if (tested.length === 0) {
    return (
      <div className="text-center py-16 space-y-2">
        <BarChart3 className="h-10 w-10 mx-auto" style={{ color: "var(--text-muted)" }} />
        <p style={{ color: "var(--text-secondary)" }}>
          Import at least one garak report to see analysis results.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {calibrations.length > 0 && (
        <div
          className="rounded-lg border p-5"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h3 className="text-sm font-semibold mb-3">Z-Score Calibration</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                  <th className="text-left px-3 py-2 font-medium">Technique</th>
                  <th className="text-left px-3 py-2 font-medium">Family</th>
                  <th className="text-right px-3 py-2 font-medium">Observed ASR</th>
                  <th className="text-right px-3 py-2 font-medium">Baseline</th>
                  <th className="text-right px-3 py-2 font-medium">Z-Score</th>
                  <th className="text-left px-3 py-2 font-medium">Severity</th>
                </tr>
              </thead>
              <tbody>
                {calibrations.map((c) => (
                  <tr key={c.technique_id} className="border-t" style={{ borderColor: "var(--border-color)" }}>
                    <td className="px-3 py-2 font-mono text-xs" style={{ color: "var(--accent)" }}>
                      {c.technique_id}
                    </td>
                    <td className="px-3 py-2 text-xs">{c.family.replace(/_/g, " ")}</td>
                    <td className="px-3 py-2 text-right font-mono">{(c.observed_asr * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                      {(c.baseline_mean * 100).toFixed(0)}%
                    </td>
                    <td className="px-3 py-2 text-right font-mono font-bold">
                      {c.z_score > 0 ? "+" : ""}{c.z_score.toFixed(2)}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`text-xs font-medium severity-${c.severity}`}>
                        {c.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {coverage && (
        <>
          <div
            className="rounded-lg border p-5"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
          >
            <h3 className="text-sm font-semibold mb-3">OWASP LLM Top 10 Coverage</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(coverage.owasp).map(([id, cat]) => (
                <div
                  key={id}
                  className="rounded-md border px-3 py-2 text-center"
                  style={{
                    backgroundColor: cat.covered ? "var(--accent-dim)" : "var(--bg-secondary)",
                    borderColor: cat.covered ? "var(--accent)" : "var(--border-color)",
                  }}
                >
                  <p className="font-mono text-xs font-bold" style={{ color: cat.covered ? "var(--accent)" : "var(--text-muted)" }}>
                    {id}
                  </p>
                  <p className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>
                    {cat.name}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {cat.tested_count}/{cat.total_techniques}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div
            className="rounded-lg border p-5"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
          >
            <h3 className="text-sm font-semibold mb-3">Attack Surface Coverage</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(coverage.attack_surface).map(([surface, data]) => {
                const pct = data.coverage_pct;
                return (
                  <div key={surface}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">{surface}</span>
                      <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                        {data.tested_count}/{data.total_count} ({pct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-2 rounded-full w-full" style={{ backgroundColor: "var(--border-color)" }}>
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${pct}%`,
                          backgroundColor:
                            pct > 60 ? "var(--accent)" : pct > 30 ? "var(--warning)" : "var(--danger)",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div
            className="rounded-lg border p-5"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
          >
            <h3 className="text-sm font-semibold mb-3">NIST AI RMF Coverage</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(coverage.nist).map(([func, data]) => (
                <div
                  key={func}
                  className="rounded-md border px-4 py-3"
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    borderColor: "var(--border-color)",
                  }}
                >
                  <p className="font-semibold text-sm">{func}</p>
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                    {data.tested_count}/{data.total_techniques} techniques
                  </p>
                  <p className="text-lg font-bold mt-1" style={{ color: "var(--accent)" }}>
                    {data.coverage_pct.toFixed(0)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
