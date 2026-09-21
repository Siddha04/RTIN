import React, { useEffect, useState } from "react";
import { api, Institution, CCTVFeed, Beneficiary, BiometricPunch } from "../api";
import { useAuth } from "../context/AuthContext";

export const NgoDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [feeds, setFeeds] = useState<CCTVFeed[]>([]);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [history, setHistory] = useState<BiometricPunch[]>([]);
  const [loading, setLoading] = useState(true);

  // Biometric punch form state
  const [shift, setShift] = useState("MORNING");
  const [staffPresent, setStaffPresent] = useState("6");
  const [staffTotal, setStaffTotal] = useState("6");
  const [benePresent, setBenePresent] = useState("54");
  const [beneTotal, setBeneTotal] = useState("58");
  const [submittingPunch, setSubmittingPunch] = useState(false);
  const [punchSuccess, setPunchSuccess] = useState<string | null>(null);

  // Incoming VC state
  const [incomingCall, setIncomingCall] = useState<any>(null);
  const [activeCall, setActiveCall] = useState<boolean>(false);

  const instId = user?.institution_id || "INS-001";

  const loadData = async () => {
    setLoading(true);
    try {
      const [instData, feedData, beneData, histData] = await Promise.all([
        api.getInstitution(instId).catch(() => null),
        api.getCctvFeeds({ institution_id: instId }),
        api.getBeneficiaries(instId),
        api.getBiometricHistory(instId)
      ]);
      setInstitution(instData);
      setFeeds(feedData);
      setBeneficiaries(beneData);
      setHistory(histData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Check for incoming surprise VC calls
    const interval = setInterval(async () => {
      try {
        const res = await api.checkIncomingVc(instId);
        if (res.has_incoming && !activeCall) {
          setIncomingCall(res);
        }
      } catch (_) {}
    }, 5000);

    return () => clearInterval(interval);
  }, [instId, activeCall]);

  const handlePunchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingPunch(true);
    setPunchSuccess(null);
    try {
      const res = await api.submitBiometricPunch({
        institution_id: instId,
        shift,
        staff_present: parseInt(staffPresent) || 0,
        staff_total: parseInt(staffTotal) || 0,
        beneficiaries_present: parseInt(benePresent) || 0,
        beneficiaries_total: parseInt(beneTotal) || 0
      });
      setPunchSuccess(`✓ ${res.message} (Recorded Attendance: ${res.attendance_rate}%)`);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to submit biometric attendance");
    } finally {
      setSubmittingPunch(false);
    }
  };

  if (loading) {
    return <div className="loading-spinner">Loading Facility Compliance Portal...</div>;
  }

  return (
    <div className="ngo-portal-container">
      {/* Incoming Surprise VC Alert Modal */}
      {incomingCall && !activeCall && (
        <div className="modal-overlay">
          <div className="modal-card incoming-call-card">
            <div className="call-ring-animation">📞</div>
            <h3>INCOMING SURPRISE INSPECTION VIDEO CALL</h3>
            <p>
              <b>Caller:</b> {incomingCall.caller_name} (Central DoSJE Ministry)
            </p>
            <p>
              <b>Target:</b> {incomingCall.target_name} ({incomingCall.target_type})
            </p>
            <small>Meeting Room Code: {incomingCall.room_code}</small>
            <div className="modal-buttons" style={{ marginTop: "1rem" }}>
              <button
                className="btn-success"
                onClick={() => {
                  setActiveCall(true);
                  setIncomingCall(null);
                }}
              >
                ✓ Accept & Start Walkthrough
              </button>
              <button className="btn-secondary" onClick={() => setIncomingCall(null)}>
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Video Walkthrough Window */}
      {activeCall && (
        <div className="card vc-active-banner" style={{ background: "#0f172a", color: "#fff", marginBottom: "1.5rem" }}>
          <div className="card-header-flex">
            <div>
              <span className="live">● LIVE WALKTHROUGH IN PROGRESS</span>
              <h3>Surprise Video Audit with Central Ministry Headquarters</h3>
              <small>Room: DOSJE-HQ-AUDIT | Watermarked GPS: 11.6643 N, 78.1460 E</small>
            </div>
            <button className="btn-danger" onClick={() => setActiveCall(false)}>
              End Video Session
            </button>
          </div>
          <div className="vc-video-mock">
            <div className="vc-stream-box">
              <span className="vc-role-tag">Central Ministry Auditor</span>
              <div className="vc-avatar">🏛</div>
            </div>
            <div className="vc-stream-box local">
              <span className="vc-role-tag">Facility Walkthrough Camera (Project Director)</span>
              <div className="vc-avatar">📹</div>
            </div>
          </div>
        </div>
      )}

      {/* Institution Facility Profile Banner */}
      <div className="command-banner ngo-banner">
        <div>
          <div className="badge-govt">DoSJE RECOGNIZED & AIDED INSTITUTION PORTAL</div>
          <h2>{institution?.name || "Mother Teresa Rehabilitation Centre for Divyangjan"}</h2>
          <p>
            <b>Scheme:</b> {institution?.scheme_category || "Deendayal Disabled Rehabilitation Scheme (DDRS)"} | <b>Sanctioned Capacity:</b> {institution?.sanctioned_capacity || 60} Beneficiaries | <b>District:</b> {institution?.district || "Salem"}
          </p>
        </div>
        <div className="banner-actions">
          <span className="badge-success">Compliance Rating: 94.2%</span>
          <span className="badge-govt">Biometric & CCTV Integrated</span>
        </div>
      </div>

      {/* 4-Camera CCTV Stream Health Section */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header-flex">
          <div>
            <h3>📹 Mandatory 4-Camera CCTV Surveillance Status</h3>
            <small>Mandated by Ministry guidelines to ensure 24/7 transparent residential monitoring</small>
          </div>
          <span className="badge-success">All Required Zones Active</span>
        </div>

        <div className="cctv-preview-grid">
          {feeds.map((cam) => (
            <div key={cam.id} className="cctv-preview-card">
              <div className="cctv-screen-mock">
                <div className="cctv-screen-label">● {cam.camera_name}</div>
                <div className="cctv-ai-badge">Observed: {cam.ai_crowd_count} Persons</div>
                <div className="cctv-facility-watermark">24FPS • 1080p • Encrypted</div>
              </div>
              <div className="cctv-card-footer">
                <span>Stream ID: {cam.id}</span>
                <span className={`status-dot ${cam.status === "ONLINE" ? "green" : "red"}`}>{cam.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="two-column-grid">
        {/* Daily Biometric Attendance Punch Form */}
        <div className="card">
          <div className="card-header-flex">
            <div>
              <h3>📝 Daily Biometric Attendance Submission</h3>
              <small>Upload shift attendance to synchronize with central DoSJE database</small>
            </div>
          </div>

          {punchSuccess && <div className="success-banner">{punchSuccess}</div>}

          <form onSubmit={handlePunchSubmit} className="form-grid">
            <div className="form-group">
              <label>Shift Timing</label>
              <select value={shift} onChange={(e) => setShift(e.target.value)}>
                <option value="MORNING">Morning Shift (08:00 AM - 02:00 PM)</option>
                <option value="EVENING">Evening Shift (02:00 PM - 08:00 PM)</option>
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Staff Present</label>
                <input
                  type="number"
                  value={staffPresent}
                  onChange={(e) => setStaffPresent(e.target.value)}
                  min="0"
                  required
                />
              </div>
              <div className="form-group">
                <label>Total Sanctioned Staff</label>
                <input
                  type="number"
                  value={staffTotal}
                  onChange={(e) => setStaffTotal(e.target.value)}
                  min="1"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Beneficiaries Present</label>
                <input
                  type="number"
                  value={benePresent}
                  onChange={(e) => setBenePresent(e.target.value)}
                  min="0"
                  required
                />
              </div>
              <div className="form-group">
                <label>Enrolled Beneficiaries</label>
                <input
                  type="number"
                  value={beneTotal}
                  onChange={(e) => setBeneTotal(e.target.value)}
                  min="1"
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={submittingPunch}>
              {submittingPunch ? "Synchronizing with Ministry..." : "✓ Submit Biometric Punch"}
            </button>
          </form>

          {/* Recent History */}
          <div style={{ marginTop: "1.5rem" }}>
            <h4>Recent Synchronization Records</h4>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Shift</th>
                    <th>Staff</th>
                    <th>Beneficiaries</th>
                    <th>CCTV Count</th>
                  </tr>
                </thead>
                <tbody>
                  {history.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: "center", color: "#64748b" }}>
                        No attendance submitted today yet.
                      </td>
                    </tr>
                  ) : (
                    history.map((h) => (
                      <tr key={h.id}>
                        <td>{h.date}</td>
                        <td><span className="badge-small">{h.shift}</span></td>
                        <td>{h.staff_present} / {h.staff_total}</td>
                        <td><b>{h.beneficiaries_present}</b> / {h.beneficiaries_total}</td>
                        <td>{h.cctv_estimated_headcount}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Verified Beneficiary Registry */}
        <div className="card">
          <div className="card-header-flex">
            <div>
              <h3>👥 Verified Beneficiary Registry</h3>
              <small>Aadhaar & biometric verified residents (Anti-Ghost Reporting)</small>
            </div>
            <span className="badge-small">{beneficiaries.length} Verified</span>
          </div>

          <div className="beneficiary-list">
            {beneficiaries.length === 0 ? (
              <p className="empty-text">No beneficiaries registered under this facility.</p>
            ) : (
              beneficiaries.map((b) => (
                <div key={b.id} className="beneficiary-card-item">
                  <div className="beneficiary-avatar">👤</div>
                  <div className="beneficiary-info">
                    <b>{b.full_name}</b>
                    <small>{b.category} • Age: {b.age} • {b.gender}</small>
                    <div className="beneficiary-meta">
                      <span>Aadhaar: {b.aadhaar_masked}</span>
                      <span className="badge-success-small">✓ Biometric Verified</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
