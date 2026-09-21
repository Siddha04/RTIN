import React, { useEffect, useState } from "react";
import { api, ComplianceNotice, AtrReport, Institution } from "../api";
import { useAuth } from "../context/AuthContext";

export const NgoCompliancePage: React.FC = () => {
  const { user } = useAuth();
  const instId = user?.institution_id || "INS-001";

  const [institution, setInstitution] = useState<Institution | null>(null);
  const [notices, setNotices] = useState<ComplianceNotice[]>([]);
  const [atrReports, setAtrReports] = useState<AtrReport[]>([]);
  const [loading, setLoading] = useState(true);

  // Submission Form State
  const [selectedNoticeId, setSelectedNoticeId] = useState<string>("");
  const [category, setCategory] = useState<string>("ATTENDANCE_VARIANCE");
  const [subject, setSubject] = useState<string>("");
  const [correctiveActions, setCorrectiveActions] = useState<string>("");
  const [directorName, setDirectorName] = useState<string>(user?.full_name || "S. Priya (Project Director)");
  const [declaration, setDeclaration] = useState<boolean>(false);
  const [fileName, setFileName] = useState<string>("compliance_documentation.pdf");
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [instData, noticesData, atrData] = await Promise.all([
        api.getInstitution(instId).catch(() => null),
        api.getComplianceNotices(instId),
        api.getAtrReports(instId)
      ]);
      setInstitution(instData);
      setNotices(noticesData);
      setAtrReports(atrData);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to load compliance records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [instId]);

  const handleSelectNoticeToRespond = (notice: ComplianceNotice) => {
    setSelectedNoticeId(notice.id);
    setSubject(`Action Taken Report: In response to ${notice.reference_no} (${notice.title})`);
    if (notice.notice_type.includes("CCTV")) {
      setCategory("CCTV_RESTORATION");
    } else if (notice.notice_type.includes("ATTENDANCE")) {
      setCategory("ATTENDANCE_VARIANCE");
    } else if (notice.notice_type.includes("UTILIZATION")) {
      setCategory("UTILIZATION_PROGRESS");
    } else {
      setCategory("INFRASTRUCTURE_SANITATION");
    }
    window.scrollTo({ top: 350, behavior: "smooth" });
  };

  const handleSubmitAtr = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!declaration) {
      alert("Please check the official declaration before submitting to the Ministry.");
      return;
    }
    setSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const sampleHash = `sha256_${Math.random().toString(36).substring(2, 10)}${Date.now().toString(36)}`;
      const res = await api.submitAtrReport({
        institution_id: instId,
        notice_id: selectedNoticeId || undefined,
        category,
        subject,
        corrective_actions: correctiveActions,
        director_name: directorName,
        supporting_hash: sampleHash,
        file_name: fileName
      });

      setSuccessMsg(`✓ ${res.message}`);
      setSubject("");
      setCorrectiveActions("");
      setSelectedNoticeId("");
      setDeclaration(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to file Action Taken Report");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="loading-spinner">Loading Ministry Compliance Portal...</div>;
  }

  return (
    <div className="ngo-portal-container">
      {/* Official Government Header Banner */}
      <div className="command-banner ngo-banner">
        <div>
          <div className="badge-govt">DoSJE GRANT-IN-AID COMPLIANCE & ATR SUBMISSION PORTAL</div>
          <h2>Government Compliance Desk & Action Taken Reporting</h2>
          <p>
            Official communication channel with the Ministry of Social Justice and Empowerment (MoSJE). Review show-cause notices, file verified Action Taken Reports (ATRs), and upload quarterly grant utilization proofs.
          </p>
          <div style={{ marginTop: "0.5rem" }}>
            <b>Institution:</b> {institution?.name || "Mother Teresa Rehabilitation Centre"} (ID: {instId}) | <b>Scheme:</b> {institution?.scheme || "DDRS"}
          </div>
        </div>
        <div className="banner-actions">
          <span className="badge-govt">Digital Certificate Verified</span>
          <span className="badge-success">Compliance Standing: Active</span>
        </div>
      </div>

      {successMsg && <div className="success-banner">{successMsg}</div>}
      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      {/* 1. Active Ministry Notices & Show-Cause Desk */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header-flex">
          <div>
            <h3>🏛 Active Ministry Notices & Discrepancy Inquiries</h3>
            <small>Directives issued by Central Ministry Monitoring Cell and State PMU inspection officers</small>
          </div>
          <span className="badge-danger">{notices.filter(n => n.status === "PENDING_RESPONSE").length} Action(s) Required</span>
        </div>

        {notices.length === 0 ? (
          <p style={{ color: "#64748b", padding: "1rem 0" }}>No outstanding notices or discrepancies from the Ministry.</p>
        ) : (
          <div className="notices-grid" style={{ display: "grid", gap: "1rem", marginTop: "1rem" }}>
            {notices.map((n) => (
              <div
                key={n.id}
                className={`compliance-notice-item notice-${n.severity.toLowerCase()}`}
                style={{
                  border: n.status === "PENDING_RESPONSE" ? "1px solid #ef4444" : "1px solid #cbd5e1",
                  borderRadius: "8px",
                  padding: "1rem 1.25rem",
                  background: n.status === "PENDING_RESPONSE" ? "#fff" : "#f8fafc"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.4rem" }}>
                      <span className={`badge-${n.severity === "HIGH" ? "danger" : n.severity === "MEDIUM" ? "warning" : "small"}`}>
                        {n.severity} PRIORITY
                      </span>
                      <span className="badge-small">{n.notice_type}</span>
                      <b style={{ color: "#334155" }}>Ref: {n.reference_no}</b>
                    </div>
                    <h4 style={{ margin: "0.2rem 0", color: "#0f172a" }}>{n.title}</h4>
                  </div>
                  <span className={`status-pill ${n.status === "PENDING_RESPONSE" ? "pill-pending" : "pill-resolved"}`}>
                    {n.status === "PENDING_RESPONSE" ? "● AWAITING NGO RESPONSE" : "✓ ATR SUBMITTED"}
                  </span>
                </div>

                <p style={{ color: "#475569", margin: "0.6rem 0", fontSize: "0.95rem" }}>{n.description}</p>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.8rem", borderTop: "1px dashed #e2e8f0", paddingTop: "0.6rem" }}>
                  <small style={{ color: "#64748b" }}>
                    <b>Issuing Cell:</b> {n.issued_by} | <b>Date:</b> {n.issued_date ? new Date(n.issued_date).toLocaleDateString() : "Recent"}
                  </small>
                  {n.status === "PENDING_RESPONSE" && (
                    <button
                      className="btn-highlight btn-small"
                      onClick={() => handleSelectNoticeToRespond(n)}
                    >
                      📝 Respond / File ATR
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. File Action Taken Report (ATR) Form */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header-flex">
          <div>
            <h3>📝 File Action Taken Report (ATR) & Compliance Rectification</h3>
            <small>Submit verified compliance explanations and documentary proof directly to MoSJE Review Officers</small>
          </div>
          {selectedNoticeId && (
            <button className="btn-secondary btn-small" onClick={() => setSelectedNoticeId("")}>
              Clear Linked Notice
            </button>
          )}
        </div>

        <form onSubmit={handleSubmitAtr} style={{ marginTop: "1rem" }}>
          <div className="form-grid">
            <div className="form-row">
              <div className="form-group">
                <label>Compliance Category</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="ATTENDANCE_VARIANCE">Shift Attendance Divergence / Biometric Reconciliation</option>
                  <option value="CCTV_RESTORATION">CCTV Surveillance Outage / Hardware Restoration</option>
                  <option value="INFRASTRUCTURE_SANITATION">Kitchen Hygiene, Nutrition & Dormitory Rectification</option>
                  <option value="UTILIZATION_PROGRESS">Quarterly Grant Utilization Progress (Form GFR 12-A)</option>
                  <option value="MEDICAL_STAFF">Medical & Caregiver Staffing Compliance</option>
                </select>
              </div>

              <div className="form-group">
                <label>Responding to Notice ID (Optional)</label>
                <select
                  value={selectedNoticeId}
                  onChange={(e) => setSelectedNoticeId(e.target.value)}
                >
                  <option value="">-- General Report / Not Linked to Specific Notice --</option>
                  {notices.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.reference_no} — {n.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Report Subject / Brief Description</label>
              <input
                type="text"
                required
                placeholder="e.g. Action Taken Report: Optical line restored for Kitchen CCTV and replacement UPS installed"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Detailed Corrective Actions Taken & Ground Explanation</label>
              <textarea
                required
                rows={5}
                placeholder="Provide a comprehensive breakdown of findings, immediate corrective steps taken, technician visits, vendor invoices, or reasons for attendance variance. Be precise for Ministry evaluation."
                value={correctiveActions}
                onChange={(e) => setCorrectiveActions(e.target.value)}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Authorizing Officer / Project Director</label>
                <input
                  type="text"
                  required
                  value={directorName}
                  onChange={(e) => setDirectorName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Supporting Evidence Attachment (PDF / JPG)</label>
                <input
                  type="text"
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  placeholder="e.g. verified_technician_bill_and_gate_photos.pdf"
                />
                <small style={{ color: "#64748b" }}>Cryptographic SHA-256 seal will be applied on upload.</small>
              </div>
            </div>

            <div className="form-group checkbox-group" style={{ background: "#f8fafc", padding: "0.8rem", borderRadius: "6px" }}>
              <label style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={declaration}
                  onChange={(e) => setDeclaration(e.target.checked)}
                  style={{ marginTop: "0.25rem" }}
                />
                <span style={{ fontSize: "0.9rem", color: "#334155" }}>
                  <b>Project Director Digital Undertaking:</b> I hereby declare that the corrective actions detailed above have been physically verified at the institution premises. I understand that submitting false declarations to the Ministry carries penalties under the GFR 2017 norms and may lead to grant suspension.
                </span>
              </label>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={submitting}
              style={{ width: "100%", padding: "0.9rem", fontSize: "1rem" }}
            >
              {submitting ? "Submitting Official ATR to Government..." : "🏛 Submit Official Action Taken Report to MoSJE Command"}
            </button>
          </div>
        </form>
      </div>

      {/* 3. Historical Submissions & Ministry Review Log */}
      <div className="card">
        <div className="card-header-flex">
          <div>
            <h3>📜 Historical ATR Submissions & Ministry Review Log</h3>
            <small>Official track record of filed compliance reports and Ministry adjudication</small>
          </div>
          <span className="badge-small">{atrReports.length} Submitted Reports</span>
        </div>

        <div className="table-responsive" style={{ marginTop: "1rem" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ATR Reference</th>
                <th>Category</th>
                <th>Subject & Scope</th>
                <th>Authorized Officer</th>
                <th>Submission Date</th>
                <th>Ministry Status</th>
                <th>Remarks / Ruling</th>
              </tr>
            </thead>
            <tbody>
              {atrReports.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", color: "#64748b" }}>
                    No Action Taken Reports filed yet.
                  </td>
                </tr>
              ) : (
                atrReports.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <b>{a.id}</b>
                      {a.notice_id && <small style={{ display: "block", color: "#64748b" }}>Notice: {a.notice_id}</small>}
                    </td>
                    <td><span className="badge-small">{a.category}</span></td>
                    <td>
                      <b>{a.subject}</b>
                      <small style={{ display: "block", color: "#64748b", maxWidth: "350px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {a.corrective_actions}
                      </small>
                    </td>
                    <td>{a.director_name}</td>
                    <td><small>{a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : "Today"}</small></td>
                    <td>
                      <span className={`status-badge-custom ${a.status === "UNDER_MINISTRY_REVIEW" ? "badge-review" : "badge-approved"}`}>
                        {a.status === "UNDER_MINISTRY_REVIEW" ? "⏳ Under Review" : "✓ Accepted"}
                      </span>
                    </td>
                    <td>
                      <small style={{ color: "#475569" }}>
                        {a.ministry_remarks || "Queued for automated review by Regional Directorate."}
                      </small>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
