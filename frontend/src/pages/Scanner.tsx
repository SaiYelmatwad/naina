import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ScanResult } from "../types/api";

export default function Scanner() {
  const [roleText, setRoleText] = useState(
    "Senior Software Engineer, backend systems. Own service architecture, mentor engineers, ship with Python and distributed systems experience."
  );
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const navigate = useNavigate();

  async function handleScan(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSaved(false);
    try {
      const r = await api.scan(roleText);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleTrack() {
    if (!result) return;
    const company = window.prompt("Company name for this application?");
    if (!company) return;
    const roleTitle = window.prompt("Role title?") || "Untitled role";
    try {
      await api.addApplication(company, roleTitle, result.score);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save application");
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-medium">Scan a role</h1>
        <p className="text-muted text-sm mt-1">
          Scored live against your saved skill profile via the real matching API.
        </p>
      </div>

      <form onSubmit={handleScan} className="bg-card border border-rule rounded-lg p-5 mb-6">
        <textarea
          value={roleText}
          onChange={(e) => setRoleText(e.target.value)}
          minLength={3}
          maxLength={8000}
          rows={5}
          className="w-full border border-rule rounded px-3 py-2 text-sm font-mono bg-paper focus:outline-none focus:ring-2 focus:ring-teal"
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-3 w-full bg-teal text-white rounded py-2.5 text-sm font-mono hover:bg-teal-deep transition-colors disabled:opacity-60"
        >
          {loading ? "Scanning…" : "Run scan"}
        </button>
      </form>

      {error && <div className="text-xs text-danger bg-danger/10 rounded px-3 py-2 mb-6">{error}</div>}

      {result && (
        <div className="bg-card border border-rule rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="font-display text-4xl font-medium">{result.score}%</div>
              <div className="font-mono text-xs text-muted mt-1">{result.verdict}</div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleTrack}
                disabled={saved}
                className="text-xs font-mono border border-rule rounded px-3 py-2 hover:border-ink disabled:opacity-50"
              >
                {saved ? "Saved ✓" : "Track this application"}
              </button>
              <button
                onClick={() => navigate("/applications")}
                className="text-xs font-mono border border-rule rounded px-3 py-2 hover:border-ink"
              >
                View applications
              </button>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-xs text-muted mb-2">MATCHED</div>
              {result.matched.length === 0 && (
                <div className="text-sm text-muted">No strong matches found.</div>
              )}
              {result.matched.map((m) => (
                <div key={m.skill} className="flex justify-between text-sm py-1.5 border-t border-rule">
                  <span>{m.skill}</span>
                  <span className="font-mono text-teal">{Math.round(m.level * 100)}%</span>
                </div>
              ))}
            </div>
            <div>
              <div className="font-mono text-xs text-muted mb-2">GAPS</div>
              {result.gaps.length === 0 && <div className="text-sm text-muted">No gaps flagged.</div>}
              {result.gaps.map((g) => (
                <div key={g.skill} className="flex justify-between text-sm py-1.5 border-t border-rule">
                  <span>{g.skill}</span>
                  <span className="font-mono text-danger">{Math.round(g.level * 100)}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-rule font-mono text-xs text-muted space-y-1">
            {result.explanation.map((line, i) => (
              <div key={i}>→ {line}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
