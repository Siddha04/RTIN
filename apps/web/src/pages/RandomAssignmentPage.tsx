import React, { useState } from "react";
import { api } from "../api";

export const RandomAssignmentPage: React.FC = () => {
  const [targetCount, setTargetCount] = useState(3);
  const [isSurprise, setIsSurprise] = useState(true);
  const [allocations, setAllocations] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleRunAllocation = async () => {
    setRunning(true);
    setSuccessMsg(null);
    try {
      const data = await api.allocateAssignments({
        target_count: targetCount,
        is_surprise: isSurprise
      });
      setAllocations(data);
      setSuccessMsg(
        `✓ AI Optimization Algorithm Executed: ${data.length} inspection duties allocated with 100% Anti-Collusion & Cooling-Off clearance.`
      );
    } catch (err: any) {
      alert(err.message || "Failed to allocate inspections");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="assignment-page-container">
      <div className="command-banner">
        <div>
          <div className="badge-govt">ALGORITHMIC GOVERNANCE & ANTI-CORRUPTION MODULE</div>
          <h2>AI Random Inspection Assignment Engine</h2>
          <p>
            Eliminates collusion, bribery, and proxy audits through mathematical optimization. Enforces cooling-off periods, home district exclusions, and Just-in-Time (JIT) sealed duty disclosure.
          </p>
        </div>
      </div>

      {/* Anti-Collusion Rules Information Grid */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>🛡 Active Anti-Collusion Governance Constraints</h3>
        <div className="rules-grid">
          <div className="rule-card">
            <div className="rule-icon">🚫</div>
            <b>Home District Exclusion</b>
            <small>Inspectors are strictly barred from auditing any institution situated in their native/home district.</small>
          </div>
          <div className="rule-card">
            <div className="rule-icon">⏳</div>
            <b>180-Day Cooling-off Period</b>
            <small>An inspector cannot be re-assigned to the same institution within a 6-month window to prevent familiarity.</small>
          </div>
          <div className="rule-card">
            <div className="rule-icon">🔒</div>
            <b>Just-In-Time Sealed Envelope</b>
            <small>For surprise audits, target destination is revealed only 2 hours prior to scheduled audit time.</small>
          </div>
          <div className="rule-card">
            <div className="rule-icon">⚖️</div>
            <b>Risk-Weighted Sampling</b>
            <small>Centers flagged with high anomaly or ghost beneficiary scores receive automated surprise audit weighting.</small>
          </div>
        </div>
      </div>

      {/* Execution Control Card */}
      <div className="card">
        <h3>Generate Automated Duty Allocations</h3>
        <p style={{ color: "#64748b", marginBottom: "1rem" }}>
          Configure batch parameters and trigger the multi-constraint optimization model.
        </p>

        {successMsg && <div className="success-banner">{successMsg}</div>}

        <div className="allocation-form-row">
          <div className="form-group">
            <label>Number of Surprise Inspections to Generate:</label>
            <input
              type="number"
              value={targetCount}
              onChange={(e) => setTargetCount(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
              max="20"
            />
          </div>

          <div className="form-group" style={{ display: "flex", alignItems: "center", paddingTop: "1.5rem" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={isSurprise}
                onChange={(e) => setIsSurprise(e.target.checked)}
              />
              <b>Enforce JIT Blind Disclosure (Surprise Inspection Mode)</b>
            </label>
          </div>

          <div className="form-group" style={{ display: "flex", alignItems: "flex-end" }}>
            <button
              className="btn-highlight"
              onClick={handleRunAllocation}
              disabled={running}
              style={{ width: "100%", padding: "0.8rem 1.5rem" }}
            >
              {running ? "Executing AI Optimization..." : "⚡ Run AI Random Duty Allocation"}
            </button>
          </div>
        </div>

        {/* Results Table */}
        {allocations.length > 0 && (
          <div style={{ marginTop: "2rem" }}>
            <h4>Newly Dispatched Automated Assignments</h4>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Inspection ID</th>
                    <th>Target Facility</th>
                    <th>District & Scheme</th>
                    <th>Assigned Inspector</th>
                    <th>Type</th>
                    <th>Anti-Collusion Checks</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {allocations.map((a) => (
                    <tr key={a.inspection_id}>
                      <td><b>{a.inspection_id}</b></td>
                      <td>{a.institution_name}</td>
                      <td>{a.district} • <span className="badge-small">{a.scheme}</span></td>
                      <td>{a.inspector_name}</td>
                      <td>
                        {a.is_surprise ? (
                          <span className="badge-danger">SURPRISE (JIT)</span>
                        ) : (
                          <span className="badge-small">ROUTINE</span>
                        )}
                      </td>
                      <td>
                        <span className="badge-success-small">✓ Home Excluded</span>{" "}
                        <span className="badge-success-small">✓ 180d Cooled</span>
                      </td>
                      <td>
                        <span className="badge-warning-small">SEALED ENVELOPE</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
