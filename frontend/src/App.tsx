import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./api/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Shell from "./components/Shell";
import AuthPage from "./pages/AuthPage";

// Dashboard pulls in Recharts (~200kB) — code-split it out of the main
// bundle so /login and the auth check don't pay for a chart library.
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Scanner = lazy(() => import("./pages/Scanner"));
const Applications = lazy(() => import("./pages/Applications"));

function PageFallback() {
  return <div className="text-sm text-muted font-mono py-10">Loading…</div>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Shell />
              </ProtectedRoute>
            }
          >
            <Route
              index
              element={
                <Suspense fallback={<PageFallback />}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route
              path="scan"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Scanner />
                </Suspense>
              }
            />
            <Route
              path="applications"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Applications />
                </Suspense>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
