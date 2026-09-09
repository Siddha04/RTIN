import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, DashboardSummary, Institution } from "../api";

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const loadDashboardData = async () => {
    try {
      const [sumData, instData] = await Promise.all([
        api.getDashboardSummary(),
        api.getInstitutions({ sort_by: "risk_desc" })
      ]);
      setSummary(sumData);
      setInstitutions(instData);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics from server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000); // 10s live polling
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading-spinner">Loading dynamic dashboard analytics...</div>;
  if (error) return <div className="error-banner">API Error: {error} <button onClick={loadDashboardData}>Retry</button></div>;

  return (
    <div>
      <div className="head">
        <div>
          <small>NATIONAL / STATE MONITORING</small>
          <h1>Dashboard</h1>
          <p>AI-prioritized inspection visibility across registered institutions.</p>
        </div>
        <button className="primary-btn" onClick={() => navigate("/inspections?action=new")}>
          + Create inspection
        </button>
      </div>

      <section className="cards-grid">
        <article className="card clickable" onClick={() => navigate("/institutions")}>
          <span>Institutions</span>
          <strong>{summary?.institutions ?? 0}</strong>
          <small>Registered target units</small>
        </article>

        <article className="card clickable high" onClick={() => navigate("/institutions?risk_band=HIGH")}>
          <span>High risk</span>
          <strong>{summary?.high_risk ?? 0}</strong>
          <small>Priority inspection target</small>
        </article>

        <article className="card clickable medium" onClick={() => navigate("/institutions?risk_band=MEDIUM")}>
          <span>Medium risk</span>
          <strong>{summary?.medium_risk ?? 0}</strong>
          <small>Frequent monitoring target</small>
        </article>

        <article className="card clickable low" onClick={() => navigate("/institutions?risk_band=LOW")}>
          <span>Low risk</span>
          <strong>{summary?.low_risk ?? 0}</strong>
          <small>Normal monitoring</small>
        </article>

        <article className="card clickable" onClick={() => navigate("/inspections")}>
          <span>Active inspections</span>
          <strong>{summary?.active_inspections ?? 0}</strong>
          <small>In-progress & assigned</small>
        </article>

        <article className="card clickable" onClick={() => navigate("/evidence")}>
          <span>Verified evidence</span>
          <strong>{summary?.verified_evidence ?? 0}</strong>
          <small>SHA-256 integrity verified</small>
        </article>

        <article className="card clickable alert-card" onClick={() => navigate("/alerts")}>
          <span>Unacknowledged Alerts</span>
          <strong>{summary?.alerts ?? 0}</strong>
          <small>Action required</small>
        </article>

        <article className="card">
          <span>Average risk score</span>
          <strong>{summary?.average_risk ?? 0} / 100</strong>
          <small>National baseline aggregate</small>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panelhead">
            <div>
              <h2>Risk intelligence</h2>
              <p>AI anomaly analysis and recommended action</p>
            </div>
            <button className="secondary-btn" onClick={() => navigate("/institutions")}>
              View All Institutions →
            </button>
          </div>
          <div className="table-rows">
            {institutions.slice(0, 5).map((inst) => (
              <div
                key={inst.id}
                className="row clickable"
                onClick={() => navigate(`/institutions/${inst.id}`)}
              >
                <i className={`dot ${inst.risk_band.toLowerCase()}`}></i>
                <div>
                  <b>{inst.name}</b>
                  <small>{inst.id} · {inst.district}</small>
                </div>
                <span className="score">{inst.risk_score}</span>
                <em className={`badge ${inst.risk_band.toLowerCase()}`}>{inst.risk_band}</em>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Risk distribution</h2>
          <p>0–30 Low · 31–60 Medium · 61–100 High</p>
          <div className="bars">
            <div>
              <i style={{ height: `${Math.max(15, ((summary?.low_risk || 0) / Math.max(1, summary?.institutions || 1)) * 100)}%` }}></i>
              <span>Low ({summary?.low_risk || 0})</span>
            </div>
            <div>
              <i style={{ height: `${Math.max(15, ((summary?.medium_risk || 0) / Math.max(1, summary?.institutions || 1)) * 100)}%` }}></i>
              <span>Medium ({summary?.medium_risk || 0})</span>
            </div>
            <div>
              <i style={{ height: `${Math.max(15, ((summary?.high_risk || 0) / Math.max(1, summary?.institutions || 1)) * 100)}%` }}></i>
              <span>High ({summary?.high_risk || 0})</span>
            </div>
          </div>
          <div className="notice">
            High-risk institutions are automatically flagged for priority or surprise inspections.
          </div>
        </article>
      </section>
    </div>
  );
};
