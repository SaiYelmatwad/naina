import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLocalError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      navigate("/");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 font-display text-xl font-semibold mb-8 justify-center">
          <span className="w-2.5 h-2.5 rounded-full bg-teal inline-block" />
          Signalwork
        </div>

        <div className="bg-card border border-rule rounded-lg p-6">
          <div className="flex gap-1 mb-6 text-sm font-mono">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`flex-1 py-2 rounded ${mode === "login" ? "bg-ink text-paper" : "text-muted"}`}
            >
              Log in
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`flex-1 py-2 rounded ${mode === "register" ? "bg-ink text-paper" : "text-muted"}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            {mode === "register" && (
              <input
                type="text"
                placeholder="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="border border-rule rounded px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-teal"
              />
            )}
            <input
              type="email"
              required
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border border-rule rounded px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-teal"
            />
            <input
              type="password"
              required
              minLength={8}
              placeholder="Password (min 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border border-rule rounded px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-teal"
            />

            {localError && (
              <div className="text-xs text-danger bg-danger/10 rounded px-3 py-2">{localError}</div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="mt-2 bg-teal text-white rounded py-2.5 text-sm font-mono hover:bg-teal-deep transition-colors disabled:opacity-60"
            >
              {submitting ? "Working…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </div>
        <p className="text-center text-xs text-muted mt-4 font-mono">
          Runs against the real Signalwork API — data persists in Postgres.
        </p>
      </div>
    </div>
  );
}
