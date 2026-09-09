import React, { useEffect, useState } from "react";
import { api } from "../api";

export const CompliancePage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCompliance = async () => {
    setLoading(true);
    try {
      const res = await api.getComplianceSummary();
      setData(res);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load compliance data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCompliance();
  }, []);

  if (loading) return <div className="loading-spinner">Auditing state compliance status...</div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <div className="head">
        <div>
          <small>STATE COMPLIANCE MONITORING</small>
          <h1>Compliance & Audit Control</h1>
          <p>Real-time audit tracking for overdue inspections, missing evidence, and record anomalies.</p>
        </div>
      </div>

      <section className="cards-grid">
        <article className="card low">
          <span>State Compliance Rate</span>
          <strong style={{ color: "#37a66a" }}>{data?.overall_compliance_rate || 0}%</strong>
          <small>Compliant institutional baseline</small>
        </article>

        <article className="card high">
          <span>High Risk Flags</span>
          <strong>{data?.high_risk_flagged || 0}</strong>
          <small>Priority surprise inspection target</small>
        </article>

        <article className="card medium">
          <span>Overdue Inspections</span>
          <strong>{data?.overdue_inspections_count || 0}</strong>
          <small>Past scheduled date</small>
        </article>

        <article className="card medium">
          <span>Abnormal AI Patterns</span>
          <strong>{data?.abnormal_records_count || 0}</strong>
          <small>Isolation Forest flags</small>
        </article>
      </section>

      <div className="grid" style={{ marginTop: "20px" }}>
        <article className="panel">
          <h2>High Risk Flagged Units Requiring Audit</h2>
          <div className="table-rows">
            {data?.high_risk_institutions?.map((inst: any) => (
              <div key={inst.id} className="row">
                <i className="dot high"></i>
                <div>
                  <b>{inst.name}</b>
                  <small>{inst.id} · {inst.district}</small>
                </div>
                <span className="score">{inst.risk_score}</span>
                <em className="badge high">HIGH RISK</em>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Unresolved Compliance Alerts</h2>
          <div className="table-rows">
            {data?.unresolved_alerts?.map((alt: any) => (
              <div key={alt.id} className="row">
                <div>
                  <b>{alt.institution_name}</b>
                  <small>{alt.message}</small>
                </div>
                <em className={`badge ${alt.severity}`}>{alt.severity.toUpperCase()}</em>
              </div>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
};
