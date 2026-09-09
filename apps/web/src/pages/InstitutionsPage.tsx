import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api, Institution } from "../api";

export const InstitutionsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingInst, setEditingInst] = useState<Partial<Institution> | null>(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const search = searchParams.get("search") || "";
  const district = searchParams.get("district") || "All";
  const riskBand = searchParams.get("risk_band") || "All";
  const sortBy = searchParams.get("sort_by") || "risk_desc";

  const navigate = useNavigate();

  const loadInstitutions = async () => {
    setLoading(true);
    try {
      const data = await api.getInstitutions({ search, district, risk_band: riskBand, sort_by: sortBy });
      setInstitutions(data);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load institutions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInstitutions();
  }, [search, district, riskBand, sortBy]);

  const handleRunAiAnalysis = async (inst: Institution) => {
    setAnalyzingId(inst.id);
    try {
      await api.analyzeAi({ institution_id: inst.id });
      await loadInstitutions();
    } catch (err: any) {
      alert(`AI Analysis Error: ${err.message}`);
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleCreateNew = () => {
    setEditingInst({
      name: "",
      district: "Salem",
      lat: 11.6643,
      lng: 78.1460,
      attendance: 50,
      beneficiaries: 300,
      inspections: 1,
      report_variance: 0.05
    });
    setShowModal(true);
  };

  const handleEdit = (inst: Institution) => {
    setEditingInst(inst);
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Are you sure you want to deactivate institution ${id}?`)) return;
    try {
      await api.deleteInstitution(id);
      await loadInstitutions();
    } catch (err: any) {
      alert(`Failed to delete: ${err.message}`);
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingInst) return;
    setFormSubmitting(true);
    try {
      if (editingInst.id) {
        await api.updateInstitution(editingInst.id, editingInst);
      } else {
        await api.createInstitution(editingInst);
      }
      setShowModal(false);
      await loadInstitutions();
    } catch (err: any) {
      alert(`Error saving institution: ${err.message}`);
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div>
      <div className="head">
        <div>
          <small>INSTITUTIONAL DIRECTORY</small>
          <h1>Registered Institutions</h1>
          <p>Real-time risk scoring, attendance monitoring, and baseline analytics.</p>
        </div>
        <button className="primary-btn" onClick={handleCreateNew}>
          + Add New Institution
        </button>
      </div>

      <div className="filters-bar">
        <input
          type="text"
          placeholder="Search institution or district..."
          value={search}
          onChange={(e) => setSearchParams({ search: e.target.value, district, risk_band: riskBand, sort_by: sortBy })}
        />

        <select
          value={district}
          onChange={(e) => setSearchParams({ search, district: e.target.value, risk_band: riskBand, sort_by: sortBy })}
        >
          <option value="All">All Districts</option>
          <option value="Salem">Salem</option>
          <option value="Erode">Erode</option>
          <option value="Namakkal">Namakkal</option>
          <option value="Coimbatore">Coimbatore</option>
          <option value="Madurai">Madurai</option>
        </select>

        <select
          value={riskBand}
          onChange={(e) => setSearchParams({ search, district, risk_band: e.target.value, sort_by: sortBy })}
        >
          <option value="All">All Risk Bands</option>
          <option value="HIGH">HIGH (61–100)</option>
          <option value="MEDIUM">MEDIUM (31–60)</option>
          <option value="LOW">LOW (0–30)</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSearchParams({ search, district, risk_band: riskBand, sort_by: e.target.value })}
        >
          <option value="risk_desc">Risk: High to Low</option>
          <option value="risk_asc">Risk: Low to High</option>
          <option value="name">Name: A to Z</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-spinner">Loading institutional registry...</div>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : (
        <div className="panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID & Name</th>
                <th>District</th>
                <th>Attendance</th>
                <th>Beneficiaries</th>
                <th>Variance</th>
                <th>Risk Score</th>
                <th>Risk Band</th>
                <th>Recommendation</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {institutions.map((inst) => (
                <tr key={inst.id}>
                  <td>
                    <b className="clickable-link" onClick={() => navigate(`/institutions/${inst.id}`)}>
                      {inst.name}
                    </b>
                    <small>{inst.id}</small>
                  </td>
                  <td>{inst.district}</td>
                  <td>{inst.attendance}%</td>
                  <td>{inst.beneficiaries}</td>
                  <td>{(inst.report_variance * 100).toFixed(1)}%</td>
                  <td>
                    <strong className="score">{inst.risk_score}</strong>
                  </td>
                  <td>
                    <span className={`badge ${inst.risk_band.toLowerCase()}`}>{inst.risk_band}</span>
                  </td>
                  <td>
                    <small>{inst.recommendation}</small>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="action-btn ai"
                        disabled={analyzingId === inst.id}
                        onClick={() => handleRunAiAnalysis(inst)}
                      >
                        {analyzingId === inst.id ? "Analyzing..." : "Run AI Analysis"}
                      </button>
                      <button className="action-btn" onClick={() => handleEdit(inst)}>Edit</button>
                      <button className="action-btn danger" onClick={() => handleDelete(inst.id)}>Deactivate</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>{editingInst?.id ? "Edit Institution" : "Add New Institution"}</h2>
            <form onSubmit={handleFormSubmit}>
              <div className="form-group">
                <label>Institution Name</label>
                <input
                  type="text"
                  required
                  value={editingInst?.name || ""}
                  onChange={(e) => setEditingInst({ ...editingInst, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>District</label>
                <input
                  type="text"
                  required
                  value={editingInst?.district || ""}
                  onChange={(e) => setEditingInst({ ...editingInst, district: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Attendance Rate (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingInst?.attendance || 0}
                    onChange={(e) => setEditingInst({ ...editingInst, attendance: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>Beneficiaries Count</label>
                  <input
                    type="number"
                    value={editingInst?.beneficiaries || 0}
                    onChange={(e) => setEditingInst({ ...editingInst, beneficiaries: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Prior Inspections Count</label>
                  <input
                    type="number"
                    value={editingInst?.inspections || 0}
                    onChange={(e) => setEditingInst({ ...editingInst, inspections: parseInt(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>Report Variance Ratio (e.g. 0.05)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editingInst?.report_variance || 0}
                    onChange={(e) => setEditingInst({ ...editingInst, report_variance: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="primary-btn" disabled={formSubmitting}>
                  {formSubmitting ? "Saving..." : "Save Institution"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
