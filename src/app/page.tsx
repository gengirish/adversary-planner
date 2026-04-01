"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Shield,
  Crosshair,
  Layers,
  Zap,
  PlusCircle,
  ArrowRight,
  Trash2,
} from "lucide-react";
import {
  type CampaignState,
  loadCampaign,
  clearCampaign,
  initCampaign,
  saveCampaign,
  fetchFamilies,
  type FamilyInfo,
} from "@/lib/api";

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div
      className="rounded-lg border p-5"
      style={{
        backgroundColor: "var(--bg-card)",
        borderColor: "var(--border-color)",
      }}
    >
      <div className="flex items-center gap-3 mb-2">
        <Icon className="h-5 w-5" style={{ color }} />
        <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
      </div>
      <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
        {value}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [campaign, setCampaign] = useState<CampaignState | null>(null);
  const [families, setFamilies] = useState<FamilyInfo[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const [formName, setFormName] = useState("");
  const [formType, setFormType] = useState("chatbot");
  const [formAccess, setFormAccess] = useState("black_box");
  const [formModeration, setFormModeration] = useState(false);
  const [formInputFilter, setFormInputFilter] = useState(false);
  const [formOutputFilter, setFormOutputFilter] = useState(false);
  const [formTools, setFormTools] = useState(false);
  const [formRag, setFormRag] = useState(false);

  useEffect(() => {
    setCampaign(loadCampaign());
    fetchFamilies().then(setFamilies).catch(() => {});
  }, []);

  const totalTechniques = families.reduce((s, f) => s + f.count, 0);

  async function handleCreate() {
    setCreating(true);
    setError("");
    try {
      const target = {
        name: formName,
        target_type: formType,
        access_level: formAccess,
        goals: ["jailbreak", "data_extraction"],
        defenses: {
          has_moderation: formModeration,
          has_input_filtering: formInputFilter,
          has_output_filtering: formOutputFilter,
        },
        capabilities: {
          has_tools: formTools,
          has_rag: formRag,
        },
      };
      const res = await initCampaign(formName, target);
      saveCampaign(res.state);
      setCampaign(res.state);
      setShowCreate(false);
      router.push("/campaign");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create campaign");
    } finally {
      setCreating(false);
    }
  }

  function handleClear() {
    clearCampaign();
    setCampaign(null);
  }

  const tested = campaign
    ? Object.values(campaign.technique_states).filter(
        (s) => s.observations > 0
      ).length
    : 0;
  const rounds = campaign?.rounds?.length ?? 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Bayesian attack planner for adaptive LLM red teaming
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={Crosshair} label="Techniques" value={totalTechniques || 49} color="var(--accent)" />
        <StatCard icon={Layers} label="Families" value={families.length || 13} color="var(--info)" />
        <StatCard icon={Shield} label="Tested" value={tested} color="var(--warning)" />
        <StatCard icon={Zap} label="Rounds" value={rounds} color="#8b5cf6" />
      </div>

      {campaign && (
        <div
          className="rounded-lg border p-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">Active Campaign</h2>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {campaign.name}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push("/campaign")}
                className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                style={{
                  backgroundColor: "var(--accent)",
                  color: "#000",
                }}
              >
                Open <ArrowRight className="h-4 w-4" />
              </button>
              <button
                onClick={handleClear}
                className="flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors border"
                style={{
                  borderColor: "var(--border-accent)",
                  color: "var(--danger)",
                }}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span style={{ color: "var(--text-muted)" }}>Target</span>
              <p>{(campaign.target as Record<string, string>).name || "—"}</p>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Rounds</span>
              <p>{rounds}</p>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Status</span>
              <p className="capitalize">{campaign.status}</p>
            </div>
          </div>
        </div>
      )}

      {!showCreate ? (
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-5 py-3 rounded-lg text-sm font-medium transition-colors border border-dashed"
          style={{
            borderColor: "var(--border-accent)",
            color: "var(--text-secondary)",
          }}
        >
          <PlusCircle className="h-5 w-5" />
          {campaign ? "Create New Campaign (replaces current)" : "Create Campaign"}
        </button>
      ) : (
        <div
          className="rounded-lg border p-6 space-y-5"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <h2 className="text-lg font-semibold">New Campaign</h2>

          {error && (
            <p className="text-sm px-3 py-2 rounded" style={{ backgroundColor: "var(--danger-dim)", color: "var(--danger)" }}>
              {error}
            </p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Campaign / Target Name</span>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Customer Support Bot"
                className="mt-1 block w-full rounded-md border px-3 py-2 text-sm outline-none"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  borderColor: "var(--border-accent)",
                  color: "var(--text-primary)",
                }}
              />
            </label>

            <label className="block">
              <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Target Type</span>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value)}
                className="mt-1 block w-full rounded-md border px-3 py-2 text-sm outline-none"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  borderColor: "var(--border-accent)",
                  color: "var(--text-primary)",
                }}
              >
                <option value="chatbot">Chatbot</option>
                <option value="assistant">Assistant</option>
                <option value="agent">Agent</option>
                <option value="api">API</option>
                <option value="rag">RAG System</option>
              </select>
            </label>

            <label className="block">
              <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Access Level</span>
              <select
                value={formAccess}
                onChange={(e) => setFormAccess(e.target.value)}
                className="mt-1 block w-full rounded-md border px-3 py-2 text-sm outline-none"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  borderColor: "var(--border-accent)",
                  color: "var(--text-primary)",
                }}
              >
                <option value="black_box">Black Box</option>
                <option value="gray_box">Gray Box</option>
                <option value="white_box">White Box</option>
              </select>
            </label>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider block mb-2" style={{ color: "var(--text-muted)" }}>Defenses & Capabilities</span>
            <div className="flex flex-wrap gap-3">
              {[
                { label: "Moderation", state: formModeration, setter: setFormModeration },
                { label: "Input Filtering", state: formInputFilter, setter: setFormInputFilter },
                { label: "Output Filtering", state: formOutputFilter, setter: setFormOutputFilter },
                { label: "Tool Use", state: formTools, setter: setFormTools },
                { label: "RAG", state: formRag, setter: setFormRag },
              ].map(({ label, state, setter }) => (
                <button
                  key={label}
                  onClick={() => setter(!state)}
                  className="px-3 py-1.5 rounded-md text-xs font-medium border transition-colors"
                  style={{
                    backgroundColor: state ? "var(--accent-dim)" : "transparent",
                    borderColor: state ? "var(--accent)" : "var(--border-accent)",
                    color: state ? "var(--accent)" : "var(--text-secondary)",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleCreate}
              disabled={!formName.trim() || creating}
              className="px-5 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-40"
              style={{ backgroundColor: "var(--accent)", color: "#000" }}
            >
              {creating ? "Creating..." : "Create Campaign"}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-5 py-2 rounded-md text-sm border"
              style={{ borderColor: "var(--border-accent)", color: "var(--text-secondary)" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {families.length > 0 && (
        <div
          className="rounded-lg border p-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <h2 className="text-lg font-semibold mb-4">Attack Families</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {families.map((f) => (
              <div
                key={f.name}
                className="rounded-md border px-4 py-3"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  borderColor: "var(--border-color)",
                }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{f.name.replace(/_/g, " ")}</span>
                  <span
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: "var(--accent-dim)",
                      color: "var(--accent)",
                    }}
                  >
                    {f.count}
                  </span>
                </div>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {f.description}
                </p>
                {f.baseline?.mean !== undefined && (
                  <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                    Baseline ASR: {(f.baseline.mean * 100).toFixed(0)}% &plusmn; {((f.baseline.std ?? 0) * 100).toFixed(0)}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
