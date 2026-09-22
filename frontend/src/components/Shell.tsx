import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";

export default function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm px-3 py-1.5 rounded-md transition-colors ${
      isActive ? "bg-ink text-paper" : "text-muted hover:text-ink"
    }`;

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-40 border-b border-rule bg-paper/90 backdrop-blur">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 font-display text-lg font-semibold">
            <span className="w-2 h-2 rounded-full bg-teal inline-block" />
            Signalwork
          </div>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
            <NavLink to="/scan" className={linkClass}>Scanner</NavLink>
            <NavLink to="/applications" className={linkClass}>Applications</NavLink>
          </nav>
          <div className="flex items-center gap-3 font-mono text-xs text-muted">
            <span>{user?.email}</span>
            <button
              onClick={handleLogout}
              className="border border-rule rounded px-3 py-1.5 hover:border-ink hover:text-ink transition-colors"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-10">
        <Outlet />
      </main>
    </div>
  );
}
