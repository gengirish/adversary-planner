"use client";

import { useEffect, useState } from "react";
import { Search, Filter, ExternalLink } from "lucide-react";
import { fetchTechniques, type TechniqueInfo } from "@/lib/api";

export default function TechniquesPage() {
  const [techniques, setTechniques] = useState<TechniqueInfo[]>([]);
  const [search, setSearch] = useState("");
  const [familyFilter, setFamilyFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTechniques()
      .then(setTechniques)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const families = [...new Set(techniques.map((t) => t.family))].sort();

  const filtered = techniques.filter((t) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      t.id.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q) ||
      t.family.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q);
    const matchesFamily = !familyFilter || t.family === familyFilter;
    return matchesSearch && matchesFamily;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p style={{ color: "var(--text-muted)" }}>Loading catalog...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-1">Technique Catalog</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          {techniques.length} techniques across {families.length} families
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
            style={{ color: "var(--text-muted)" }}
          />
          <input
            type="text"
            placeholder="Search techniques..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border pl-10 pr-3 py-2 text-sm outline-none"
            style={{
              backgroundColor: "var(--bg-card)",
              borderColor: "var(--border-color)",
              color: "var(--text-primary)",
            }}
          />
        </div>
        <div className="relative">
          <Filter
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
            style={{ color: "var(--text-muted)" }}
          />
          <select
            value={familyFilter}
            onChange={(e) => setFamilyFilter(e.target.value)}
            className="rounded-md border pl-10 pr-8 py-2 text-sm outline-none appearance-none"
            style={{
              backgroundColor: "var(--bg-card)",
              borderColor: "var(--border-color)",
              color: "var(--text-primary)",
            }}
          >
            <option value="">All families</option>
            {families.map((f) => (
              <option key={f} value={f}>
                {f.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        className="rounded-lg border overflow-hidden"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border-color)",
        }}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr
                className="text-left text-xs uppercase tracking-wider"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  color: "var(--text-muted)",
                }}
              >
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Technique</th>
                <th className="px-4 py-3 font-medium">Family</th>
                <th className="px-4 py-3 font-medium">ATLAS</th>
                <th className="px-4 py-3 font-medium">OWASP</th>
                <th className="px-4 py-3 font-medium">Probes</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, i) => (
                <tr
                  key={t.id}
                  className="border-t transition-colors"
                  style={{
                    borderColor: "var(--border-color)",
                    backgroundColor:
                      i % 2 === 0 ? "transparent" : "var(--bg-secondary)",
                  }}
                >
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--accent)" }}>
                    {t.id}
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium">{t.name}</p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {t.description}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block px-2 py-0.5 rounded text-xs"
                      style={{
                        backgroundColor: "var(--accent-dim)",
                        color: "var(--accent)",
                      }}
                    >
                      {t.family.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                    {t.atlas_technique || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {t.owasp_categories.map((c) => (
                        <span
                          key={c}
                          className="px-1.5 py-0.5 rounded text-xs"
                          style={{
                            backgroundColor: "var(--info-dim)",
                            color: "var(--info)",
                          }}
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: "var(--text-muted)" }}>
                    {t.garak_probes.length > 0
                      ? t.garak_probes.map((p) => p.replace("probes.", "")).join(", ")
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12">
            <p style={{ color: "var(--text-muted)" }}>No techniques match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
