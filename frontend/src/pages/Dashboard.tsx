import { useEffect, useState, type FormEvent } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";
import type { Skill } from "../types/api";

const CATEGORIES = ["general", "systems", "ml", "leadership", "coding", "product"];

export default function Dashboard() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [level, setLevel] = useState(0.5);
  const [category, setCategory] = useState("general");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listSkills();
      setSkills(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listSkills();
        if (!cancelled) setSkills(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load skills");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.addSkill(name.trim().toLowerCase(), level, category);
      setName("");
      setLevel(0.5);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add skill");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await api.deleteSkill(id);
      setSkills((prev) => prev.filter((s) => s.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete skill");
    }
  }

  const radarData = skills.slice(0, 8).map((s) => ({
    subject: s.name,
    level: Math.round(s.level * 100),
  }));

  return (
    <div>
      <div className="mb-10">
        <h1 className="font-display text-3xl font-medium">Your skill profile</h1>
        <p className="text-muted text-sm mt-1">
          Skills you add here are what every job scan is scored against.
        </p>
      </div>

      {error && (
        <div className="text-xs text-danger bg-danger/10 rounded px-3 py-2 mb-6">{error}</div>
      )}

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <form
            onSubmit={handleAdd}
            className="bg-card border border-rule rounded-lg p-5 flex flex-col gap-3 mb-6"
          >
            <div className="font-mono text-xs text-muted">ADD SKILL</div>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. distributed systems"
              required
              maxLength={120}
              className="border border-rule rounded px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-teal"
            />
            <div className="flex gap-3 items-center">
              <label className="text-xs text-muted font-mono w-24">
                Level {Math.round(level * 100)}%
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={level}
                onChange={(e) => setLevel(parseFloat(e.target.value))}
                className="flex-1"
              />
            </div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="border border-rule rounded px-3 py-2 text-sm bg-paper"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={submitting}
              className="bg-teal text-white rounded py-2 text-sm font-mono hover:bg-teal-deep transition-colors disabled:opacity-60"
            >
              {submitting ? "Adding…" : "Add skill"}
            </button>
          </form>

          <div className="bg-card border border-rule rounded-lg divide-y divide-rule">
            {loading && <div className="p-4 text-sm text-muted">Loading…</div>}
            {!loading && skills.length === 0 && (
              <div className="p-4 text-sm text-muted">No skills yet — add your first one above.</div>
            )}
            {skills.map((s) => (
              <div key={s.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <div className="text-sm font-medium">{s.name}</div>
                  <div className="text-xs text-muted font-mono">
                    {s.category} · {Math.round(s.level * 100)}%
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="text-xs text-danger font-mono hover:underline"
                >
                  remove
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-card border border-rule rounded-lg p-5">
          <div className="font-mono text-xs text-muted mb-4">SKILL SIGNAL (first 8)</div>
          {radarData.length >= 3 ? (
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData} outerRadius="75%">
                <PolarGrid stroke="var(--color-rule)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fontSize: 10, fill: "var(--color-muted)" }}
                />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar
                  dataKey="level"
                  stroke="var(--color-teal)"
                  fill="var(--color-teal)"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-sm text-muted py-16 text-center">
              Add at least 3 skills to see the radar chart.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
