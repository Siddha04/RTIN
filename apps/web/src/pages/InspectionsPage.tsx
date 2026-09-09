import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, Inspection, Institution } from "../api";

export const InspectionsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showModal, setShowModal] = useState(searchParams.get("action") === "new");
  const [instId, setInstId] = useState(searchParams.get("institution_id") || "");
  const [inspector, setInspector] = useState("A. Kumar");
  const [priority, setPriority] = useState(false);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const statusFilter = searchParams.get("status") || "All";

  const loadData = async () => {
    setLoading(true);
    try {
      const [inspData, instData] = await Promise.all([
        api.getInspections({ status: statusFilter }),
        api.getInstitutions()
      ]);
      setInspections(inspData);
      setInstitutions(instData);
      if (!instId && instData.length > 0) {
        setInstId(instData[0].id);
      }
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load inspections");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleCreateInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createInspection({
        institution_id: instId,
        inspector_name: inspector,
        priority,
        notes
      });
      setShowModal(false);
      setNotes("");
      await loadData();
    } catch (err: any) {
      alert(`Error creating inspection: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await api.updateInspection(id, { status: newStatus });
      await loadData();
    } catch (err: any) {
      alert(`Error updating status: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="head">
        <div>
          <small>FIELD OPERATIONS</small>
          <h1>Inspection Management</h1>
          <p>Schedule, assign, and track field inspections across high and medium risk institutions.</p>
        </div>
        <button className="primary-btn" onClick={() => setShowModal(true)}>
          + Schedule New Inspection
        </button>
      </div>

      <div className="filters-bar">
        <select
          value={statusFilter}
          onChange={(e) => setSearchParams({ status: e.target.value })}
        >
          <option value="All">All Statuses</option>
          <option value="assigned">Assigned</option>
          <option value="priority">Priority</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-spinner">Loading field inspections queue...</div>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : (
        <div className="panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Inspection ID</th>
                <th>Institution</th>
                <th>District</th>
                <th>Assigned Inspector</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Scheduled Date</th>
                <th>Update Status</th>
              </tr>
            </thead>
            <tbody>
              {inspections.map((insp) => (
                <tr key={insp.id}>
                  <td><b>{insp.id}</b></td>
                  <td>{insp.institution_name}</td>
                  <td>{insp.district}</td>
                  <td>{insp.inspector}</td>
                  <td>
                    {insp.priority ? (
                      <span className="badge high">PRIORITY</span>
                    ) : (
                      <span className="badge low">NORMAL</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${insp.status}`}>{insp.status.toUpperCase()}</span>
                  </td>
                  <td>
                    <small>{insp.scheduled_at ? new Date(insp.scheduled_at).toLocaleString() : "TBD"}</small>
                  </td>
                  <td>
                    <select
                      className="status-select"
                      value={insp.status}
                      onChange={(e) => handleStatusChange(insp.id, e.target.value)}
                    >
                      <option value="assigned">Assigned</option>
                      <option value="priority">Priority</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                    </select>
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
            <h2>Schedule New Field Inspection</h2>
            <form onSubmit={handleCreateInspection}>
              <div className="form-group">
                <label>Select Target Institution</label>
                <select value={instId} onChange={(e) => setInstId(e.target.value)}>
                  {institutions.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.name} ({i.district}) - Risk: {i.risk_score} [{i.risk_band}]
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Assigned Field Inspector</label>
                <select value={inspector} onChange={(e) => setInspector(e.target.value)}>
                  <option value="A. Kumar">A. Kumar (Senior Officer)</option>
                  <option value="S. Priya">S. Priya (Regional Inspector)</option>
                  <option value="M. Ravi">M. Ravi (Field Auditor)</option>
                  <option value="R. Sharma">R. Sharma (Surprise Inspector)</option>
                </select>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={priority}
                    onChange={(e) => setPriority(e.target.checked)}
                  />
                  Mark as High Priority / Surprise Inspection
                </label>
              </div>

              <div className="form-group">
                <label>Inspection Notes & Scope</label>
                <textarea
                  rows={3}
                  placeholder="Enter specific audit instructions..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="primary-btn" disabled={submitting}>
                  {submitting ? "Scheduling..." : "Assign Inspection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
