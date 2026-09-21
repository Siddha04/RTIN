import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, Institution, Inspection, AlertItem } from "../api";

export const DistrictDashboardPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.getInstitutions({ district: "Salem" }),
      api.getInspections(),
      api.getAlerts()
    ]).then(([insts, insps, alts]) => {
      setInstitutions(insts);
      setInspections(insps.filter((i) => i.district === "Salem" || !i.district));
      setAlerts(alts);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="loading-spinner">Loading District Social Welfare Console...</div>;
  }

  return (
    <div className="district-console-container">
      <div className="command-banner">
        <div>
          <div className="badge-govt">DISTRICT SOCIAL WELFARE OFFICER (DSWO) CONSOLE</div>
          <h2>District Social Welfare Administration — Salem District</h2>
          <p>
            Local governance of aided institutions, PMU field inspector deployments, ground grievance resolutions, and compliance monitoring.
          </p>
        </div>
        <div className="banner-actions">
          <button className="btn-primary" onClick={() => navigate("/risk-map")}>
            🗺 District GIS Map
          </button>
          <button className="btn-secondary" onClick={() => navigate("/institutions")}>
            🏢 District Aided Centers
          </button>
        </div>
      </div>

      {/* District KPIs */}
      <div className="kpi-grid">
        <div className="card kpi">
          <div className="kpi-icon">🏢</div>
          <div className="kpi-content">
            <span className="kpi-title">District Aided Centers</span>
            <b>{institutions.length} Centers</b>
            <small>DDRS, Senior Citizens, Hostels</small>
          </div>
        </div>
        <div className="card kpi">
          <div className="kpi-icon">👥</div>
          <div className="kpi-content">
            <span className="kpi-title">Enrolled Beneficiaries</span>
            <b>{institutions.reduce((acc, i) => acc + i.beneficiaries, 0)}</b>
            <small>Registered in District Database</small>
          </div>
        </div>
        <div className="card kpi">
          <div className="kpi-icon">📋</div>
          <div className="kpi-content">
            <span className="kpi-title">PMU Audits Completed</span>
            <b style={{ color: "#10b981" }}>{inspections.filter((i) => i.status === "completed").length} Audits</b>
            <small>Quarterly Target Achieved</small>
          </div>
        </div>
        <div className="card kpi">
          <div className="kpi-icon">🚨</div>
          <div className="kpi-content">
            <span className="kpi-title">Pending Citizen Complaints</span>
            <b style={{ color: "#f59e0b" }}>{alerts.length} Inquiries</b>
            <small>Assigned to Field Squads</small>
          </div>
        </div>
      </div>

      {/* District Institutions Table */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header-flex">
          <div>
            <h3>District Aided NGOs & Residential Centers</h3>
            <small>Direct oversight and monitoring under District Social Welfare purview</small>
          </div>
          <Link to="/institutions" className="btn-small">View Full Registry →</Link>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Center ID</th>
                <th>Institution Name</th>
                <th>Scheme</th>
                <th>Beneficiaries</th>
                <th>Attendance</th>
                <th>Risk Band</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {institutions.map((i) => (
                <tr key={i.id}>
                  <td><b>{i.id}</b></td>
                  <td>{i.name}</td>
                  <td><span className="badge-small">{i.scheme || "DDRS"}</span></td>
                  <td>{i.beneficiaries}</td>
                  <td>{i.attendance}%</td>
                  <td>
                    <span className={`badge-risk ${i.risk_band?.toLowerCase()}`}>
                      {i.risk_band}
                    </span>
                  </td>
                  <td>
                    <Link to={`/institutions/${i.id}`} className="btn-action-small">
                      View Dossier →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
