import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Application } from "../types/api";

const PAGE_SIZE = 10;

const STATUS_COLORS: Record<string, string> = {
  applied: "text-muted",
  interview: "text-amber",
  offer: "text-teal",
  rejected: "text-danger",
};

export default function Applications() {
  const [items, setItems] = useState<Application[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await api.listApplicationsPage(page, PAGE_SIZE);
        if (cancelled) return;
        setItems(result.items);
        setTotal(result.meta.total);
        setHasNext(result.meta.has_next);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load applications");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [page]);

  return (
    <div>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl font-medium">Applications</h1>
          <p className="text-muted text-sm mt-1">{total} tracked · saved from the scanner</p>
        </div>
      </div>

      {error && <div className="text-xs text-danger bg-danger/10 rounded px-3 py-2 mb-6">{error}</div>}

      <div className="bg-card border border-rule rounded-lg divide-y divide-rule">
        {loading && <div className="p-4 text-sm text-muted">Loading…</div>}
        {!loading && items.length === 0 && (
          <div className="p-4 text-sm text-muted">
            No applications tracked yet — run a scan and click "Track this application".
          </div>
        )}
        {items.map((a) => (
          <div key={a.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <div className="text-sm font-medium">{a.role_title}</div>
              <div className="text-xs text-muted font-mono">{a.company}</div>
            </div>
            <div className="flex items-center gap-4">
              {a.match_score !== null && (
                <span className="font-mono text-xs text-muted">{Math.round(a.match_score)}%</span>
              )}
              <span className={`font-mono text-xs ${STATUS_COLORS[a.status] ?? "text-muted"}`}>
                {a.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-4 font-mono text-xs text-muted">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="border border-rule rounded px-3 py-1.5 disabled:opacity-40"
          >
            ← Prev
          </button>
          <span>Page {page}</span>
          <button
            disabled={!hasNext}
            onClick={() => setPage((p) => p + 1)}
            className="border border-rule rounded px-3 py-1.5 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
