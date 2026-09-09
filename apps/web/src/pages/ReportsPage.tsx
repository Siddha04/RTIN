import React, { useEffect, useState } from "react";
import { api } from "../api";

export const ReportsPage: React.FC = () => {
  const [district, setDistrict] = useState("All");
  const [riskBand, setRiskBand] = useState("All");
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await api.getReportsSummary({ district, risk_band: riskBand });
      setReportData(data);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load report data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [district, riskBand]);

  const handleExportCsv = () => {
    const url = api.getExportUrl("csv", district === "All" ? undefined : district, riskBand === "All" ? undefined : riskBand);
    window.open(url, "_blank");
  };

  const handleExportJson = () => {
    const url = api.getExportUrl("json", district === "All" ? undefined : district, riskBand === "All" ? undefined : riskBand);
    window.open(url, "_blank");
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="printable-report">
      <div className="head no-print">
        <div>
          <small>EXECUTIVE REPORTING</small>
          <h1>State Analytics & Compliance Reports</h1>
          <p>Generate, review, and export risk assessment reports across institutions.</p>
        </div>
        <div className="button-group">
          <button className="secondary-btn" onClick={handleExportJson}>Export JSON</button>
          <button className="secondary-btn" onClick={handleExportCsv}>Export CSV</button>
          <button className="primary-btn" onClick={handlePrint}>Print Report</button>
        </div>
      </div>

      <div className="filters-bar no-print">
        <select value={district} onChange={(e) => setDistrict(e.target.value)}>
          <option value="All">All Districts</option>
          <option value="Salem">Salem</option>
          <option value="Erode">Erode</option>
          <option value="Namakkal">Namakkal</option>
          <option value="Coimbatore">Coimbatore</option>
        </select>

        <select value={riskBand} onChange={(e) => setRiskBand(e.target.value)}>
          <option value="All">All Risk Bands</option>
          <option value="HIGH">HIGH (61-100)</option>
          <option value="MEDIUM">MEDIUM (31-60)</option>
          <option value="LOW">LOW (0-30)</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-spinner">Generating report metrics...</div>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : (
        <div>
          <section className="cards-grid" style={{ marginBottom: "20px" }}>
            <article className="card">
              <span>Total Units</span>
              <strong>{reportData?.total_institutions || 0}</strong>
            </article>

            <article className="card high">
              <span>High Risk Units</span>
              <strong>{reportData?.high_risk_count || 0}</strong>
            </article>

            <article className="card medium">
              <span>Medium Risk Units</span>
              <strong>{reportData?.medium_risk_count || 0}</strong>
            </article>

            <article className="card low">
              <span>Low Risk Units</span>
              <strong>{reportData?.low_risk_count || 0}</strong>
            </article>

            <article className="card">
              <span>Total Inspections</span>
              <strong>{reportData?.total_inspections || 0}</strong>
            </article>

            <article className="card">
              <span>Evidence Verified Rate</span>
              <strong>{reportData?.evidence_verified_rate || 0}%</strong>
            </article>
          </section>

          <div className="panel">
            <h2>Detailed Institutional Risk Breakdown</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>District</th>
                  <th>Attendance</th>
                  <th>Beneficiaries</th>
                  <th>Risk Score</th>
                  <th>Risk Band</th>
                  <th>AI Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {reportData?.institutions?.map((inst: any) => (
                  <tr key={inst.id}>
                    <td><b>{inst.id}</b></td>
                    <td>{inst.name}</td>
                    <td>{inst.district}</td>
                    <td>{inst.attendance}%</td>
                    <td>{inst.beneficiaries}</td>
                    <td><strong className="score">{inst.risk_score}</strong></td>
                    <td><span className={`badge ${inst.risk_band.toLowerCase()}`}>{inst.risk_band}</span></td>
                    <td><small>{inst.recommendation}</small></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
