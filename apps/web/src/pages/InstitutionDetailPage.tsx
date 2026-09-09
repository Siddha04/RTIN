import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Institution } from "../api";

export const InstitutionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [inst, setInst] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const navigate = useNavigate();

  const loadDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await api.getInstitution(id);
      setInst(data);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load institution details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [id]);

  const handleRunAi = async () => {
    if (!id) return;
    setAnalyzing(true);
    try {
      await api.analyzeAi({ institution_id: id });
      await loadDetail();
    } catch (err: any) {
      alert(`AI error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="loading-spinner">Loading institution file...</div>;
  if (error) return <div className="error-banner">Error: {error}</div>;
  if (!inst) return <div className="error-banner">Institution not found</div>;

  return (
    <div>
      <div className="head">
        <div>
          <small>INSTITUTION PROFILE · {inst.id}</small>
          <h1>{inst.name}</h1>
          <p>{inst.district} District · Coordinates: ({inst.lat}, {inst.lng})</p>
        </div>
        <div className="button-group">
          <button className="secondary-btn" onClick={() => navigate("/institutions")}>
            ← Back to Directory
          </button>
          <button className="primary-btn" onClick={handleRunAi} disabled={analyzing}>
            {analyzing ? "Running AI..." : "Re-run AI Risk Analysis"}
          </button>
        </div>
      </div>

      <section className="cards-grid">
        <article className="card">
          <span>Risk Score</span>
          <strong className="score">{inst.risk_score} / 100</strong>
          <em className={`badge ${inst.risk_band.toLowerCase()}`}>{inst.risk_band} RISK</em>
        </article>

        <article className="card">
          <span>Attendance Rate</span>
          <strong>{inst.attendance}%</strong>
          <small>Recorded attendance baseline</small>
        </article>

        <article className="card">
          <span>Beneficiaries</span>
          <strong>{inst.beneficiaries}</strong>
          <small>Enrolled citizens</small>
        </article>

        <article className="card">
          <span>Report Variance</span>
          <strong>{(inst.report_variance * 100).toFixed(1)}%</strong>
          <small>Historical record deviation</small>
        </article>
      </section>

      <section className="grid" style={{ marginTop: "20px" }}>
        <article className="panel">
          <h2>AI Anomaly Intelligence</h2>
          <div className="detail-meta">
            <div className="meta-item">
              <label>Anomaly Detected:</label>
              <span>{inst.anomaly ? "⚠️ YES (Unusual baseline pattern)" : "✅ NO (Normal pattern)"}</span>
            </div>
            <div className="meta-item">
              <label>Anomaly Score:</label>
              <span>{inst.anomaly_score}</span>
            </div>
            <div className="meta-item">
              <label>Recommendation:</label>
              <b>{inst.recommendation}</b>
            </div>
            <div className="meta-item">
              <label>Detected Reason:</label>
              <p>{inst.reason}</p>
            </div>
            <div className="meta-item">
              <label>Last Analyzed:</label>
              <small>{inst.analyzed_at ? new Date(inst.analyzed_at).toLocaleString() : "Just now"}</small>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Inspection & Evidence History</h2>
          <div className="detail-meta">
            <div className="meta-item">
              <label>Verified Evidence Submissions:</label>
              <span>{inst.evidence_count || 0} Records</span>
            </div>
          </div>

          <div style={{ marginTop: "15px" }}>
            <h3 style={{ fontSize: "14px", marginBottom: "10px" }}>Scheduled / Past Inspections</h3>
            {inst.history && inst.history.length > 0 ? (
              <div className="table-rows">
                {inst.history.map((h: any) => (
                  <div key={h.id} className="row">
                    <div>
                      <b>{h.id}</b>
                      <small>Inspector: {h.inspector}</small>
                    </div>
                    <em className={`badge ${h.status}`}>{h.status.toUpperCase()}</em>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "12px", color: "#7c90a0" }}>No inspection history on record.</p>
            )}
            <button
              className="primary-btn"
              style={{ width: "100%", marginTop: "15px" }}
              onClick={() => navigate(`/inspections?action=new&institution_id=${inst.id}`)}
            >
              + Schedule New Inspection for this Unit
            </button>
          </div>
        </article>
      </section>
    </div>
  );
};
