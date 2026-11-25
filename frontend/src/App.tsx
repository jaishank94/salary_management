import { useEffect, useState } from "react";
import { MotionConfig, motion } from "framer-motion";
import { ChartColumn, Compass, Menu, Users, X } from "lucide-react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api } from "./api";
import { ReferenceProvider, ToastProvider } from "./context";
import { DirectoryPage } from "./pages/DirectoryPage";
import { InsightsPage } from "./pages/InsightsPage";
import type { ReferenceData } from "./types";

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        <ReferenceGate />
      </ToastProvider>
    </MotionConfig>
  );
}

function ReferenceGate() {
  const [reference, setReference] = useState<ReferenceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    api<ReferenceData>("/reference", { signal: controller.signal })
      .then(setReference)
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setError(caught instanceof Error ? caught.message : "Northstar can't reach the server.");
      });
    return () => controller.abort();
  }, [attempt]);

  if (error) {
    return (
      <div className="boot">
        <Compass size={28} />
        <h1>Northstar is offline</h1>
        <p>{error}</p>
        <button type="button" className="btn btn-primary" onClick={() => setAttempt((value) => value + 1)}>
          Try again
        </button>
      </div>
    );
  }
  if (!reference) {
    return (
      <div className="boot">
        <div className="skeleton boot-skeleton" />
        <p>Opening Northstar…</p>
      </div>
    );
  }
  return (
    <ReferenceProvider value={reference}>
      <Shell />
    </ReferenceProvider>
  );
}

function Shell() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <div className="shell">
      <a className="skip" href="#content">
        Skip to content
      </a>
      <header className="mobile-bar">
        <span className="brand-mark">
          <Compass size={18} /> Northstar
        </span>
        <button type="button" className="icon-btn" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((value) => !value)}>
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </header>
      {open ? <button type="button" className="nav-scrim" aria-label="Close menu" onClick={() => setOpen(false)} /> : null}
      <aside className={open ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <span className="brand-badge" aria-hidden="true">
            <Compass size={18} />
          </span>
          <div>
            <strong>Northstar</strong>
            <small>Salary management</small>
          </div>
        </div>
        <nav aria-label="Primary">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
            <ChartColumn size={18} /> Insights
          </NavLink>
          <NavLink to="/people" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
            <Users size={18} /> People
          </NavLink>
        </nav>
        <p className="sidebar-note">Demo workspace. Sign-in is not enabled, so keep real employee data out of this copy.</p>
      </aside>
      <main id="content" className="content">
        <motion.div key={location.pathname} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
          <Routes location={location}>
            <Route path="/" element={<InsightsPage />} />
            <Route path="/people" element={<DirectoryPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </motion.div>
      </main>
    </div>
  );
}
