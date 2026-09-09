import React, { useEffect, useState } from "react";
import { api, AlertItem } from "../api";

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(filter === "All" ? undefined : filter);
      setAlerts(data);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      await loadAlerts();
    } catch (err: any) {
      alert(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="head">
        <div>
          <small>REAL-TIME ALERT CENTER</small>
          <h1>System Alerts</h1>
          <p>Automated alerts triggered by AI high-risk scores, record anomalies, and evidence check failures.</p>
        </div>
        <div className="button-group">
          <button className={`secondary-btn ${filter === "All" ? "active" : ""}`} onClick={() => setFilter("All")}>
            All Alerts
          </button>
          <button className={`secondary-btn ${filter === "unacknowledged" ? "active" : ""}`} onClick={() => setFilter("unacknowledged")}>
            Unacknowledged
          </button>
          <button className={`secondary-btn ${filter === "acknowledged" ? "active" : ""}`} onClick={() => setFilter("acknowledged")}>
            Acknowledged
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner">Loading alert queue...</div>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : (
        <div className="panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Alert ID</th>
                <th>Target Institution</th>
                <th>Alert Type</th>
                <th>Severity</th>
                <th>Alert Message</th>
                <th>Triggered Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alt) => (
                <tr key={alt.id}>
                  <td><b>{alt.id}</b></td>
                  <td>{alt.institution_name}</td>
                  <td><code>{alt.type}</code></td>
                  <td>
                    <span className={`badge ${alt.severity}`}>{alt.severity.toUpperCase()}</span>
                  </td>
                  <td>{alt.message}</td>
                  <td><small>{new Date(alt.created_at).toLocaleString()}</small></td>
                  <td>
                    <em className={`badge ${alt.status === "acknowledged" ? "low" : "high"}`}>
                      {alt.status.toUpperCase()}
                    </em>
                  </td>
                  <td>
                    {alt.status === "unacknowledged" ? (
                      <button className="primary-btn" style={{ fontSize: "11px", padding: "4px 8px" }} onClick={() => handleAcknowledge(alt.id)}>
                        Acknowledge
                      </button>
                    ) : (
                      <small style={{ color: "#8295a5" }}>Acknowledged</small>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
