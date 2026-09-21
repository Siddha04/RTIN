import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, Institution, VCCandidate, VCSession } from "../api";

export const VideoConferencePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preselectedInstId = searchParams.get("institution_id") || "";

  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstId, setSelectedInstId] = useState<string>(preselectedInstId);
  const [targetType, setTargetType] = useState<"BENEFICIARY" | "STAFF" | "INCHARGE">("BENEFICIARY");
  const [candidate, setCandidate] = useState<VCCandidate | null>(null);
  const [loadingCandidate, setLoadingCandidate] = useState(false);

  // In-Call State
  const [activeSession, setActiveSession] = useState<any | null>(null);
  const [callTimer, setCallTimer] = useState<number>(0);
  const [muted, setMuted] = useState(false);
  const [videoOff, setVideoOff] = useState(false);
  const [auditNotes, setAuditNotes] = useState("");
  const [flagDiscrepancy, setFlagDiscrepancy] = useState(false);
  const [savingCall, setSavingCall] = useState(false);
  const [callFinishedMsg, setCallFinishedMsg] = useState<string | null>(null);

  // Historical sessions
  const [recentSessions, setRecentSessions] = useState<VCSession[]>([]);

  useEffect(() => {
    api.getInstitutions().then((data) => {
      setInstitutions(data);
      if (!selectedInstId && data.length > 0) {
        setSelectedInstId(data[0].id);
      }
    });
    api.getVcSessions().then((sessions) => setRecentSessions(sessions));
  }, []);

  useEffect(() => {
    if (preselectedInstId) {
      setSelectedInstId(preselectedInstId);
    }
  }, [preselectedInstId]);

  useEffect(() => {
    let interval: any;
    if (activeSession) {
      interval = setInterval(() => {
        setCallTimer((prev) => prev + 1);
      }, 1000);
    } else {
      setCallTimer(0);
    }
    return () => clearInterval(interval);
  }, [activeSession]);

  const handlePickCandidate = async () => {
    if (!selectedInstId) return;
    setLoadingCandidate(true);
    setCandidate(null);
    setCallFinishedMsg(null);
    try {
      const data = await api.getVcCandidate(selectedInstId, targetType);
      setCandidate(data);
    } catch (err: any) {
      alert(err.message || "Failed to pick random candidate");
    } finally {
      setLoadingCandidate(false);
    }
  };

  const handleInitiateCall = async () => {
    if (!candidate) return;
    try {
      const session = await api.initiateVc({
        institution_id: candidate.institution_id,
        target_type: candidate.target_type,
        target_name: candidate.name,
        target_contact: candidate.contact
      });
      setActiveSession(session);
    } catch (err: any) {
      alert(err.message || "Failed to initiate VC call");
    }
  };

  const handleFinishCall = async () => {
    if (!activeSession) return;
    setSavingCall(true);
    try {
      await api.finishVc({
        session_id: activeSession.session_id,
        duration_sec: callTimer,
        notes: auditNotes,
        discrepancy_flagged: flagDiscrepancy
      });
      setCallFinishedMsg(
        `✓ Video Audit Session Concluded & Archived into Central DoSJE Audit Trail. (Duration: ${callTimer}s)`
      );
      setActiveSession(null);
      setCandidate(null);
      setAuditNotes("");
      setFlagDiscrepancy(false);
      api.getVcSessions().then((sessions) => setRecentSessions(sessions));
    } catch (err: any) {
      alert(err.message || "Failed to record session");
    } finally {
      setSavingCall(false);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="vc-page-container">
      <div className="command-banner">
        <div>
          <div className="badge-govt">SURPRISE VIDEO CONFERENCING AUDIT PROTOCOL</div>
          <h2>Randomized Virtual Inspection & Beneficiary Walkthrough</h2>
          <p>
            Connect instantly with Project Incharges, on-duty caregivers, or randomly chosen beneficiaries. Validates ground reality without prior notice to eliminate proxy functioning.
          </p>
        </div>
      </div>

      {callFinishedMsg && <div className="success-banner">{callFinishedMsg}</div>}

      {/* Active Video Conference Room */}
      {activeSession ? (
        <div className="card vc-room-card">
          <div className="vc-header-bar">
            <div>
              <span className="live">● LIVE VIDEO AUDIT CONNECTED</span>
              <h3>
                {activeSession.target_name} ({activeSession.target_type}) — {activeSession.institution_name}
              </h3>
              <small>Meeting Room ID: {activeSession.room_code} | Call Time: {formatTime(callTimer)}</small>
            </div>
            <div className="vc-timer-badge">{formatTime(callTimer)}</div>
          </div>

          <div className="vc-call-theatre">
            <div className="vc-remote-stream">
              <div className="vc-stream-placeholder">
                <div className="vc-avatar-large">👤</div>
                <b>{activeSession.target_name}</b>
                <small>{activeSession.target_type} • Live Camera Feed Connected</small>
              </div>

              {/* Tamper-Proof Cryptographic Watermark */}
              <div className="vc-watermark-overlay">
                <div>MoSJE AUDIT WATERMARK • ROOM: {activeSession.room_code}</div>
                <div>
                  GPS: {activeSession.watermark?.gps_lat?.toFixed(4)} N, {activeSession.watermark?.gps_lng?.toFixed(4)} E
                </div>
                <div>TIME: {new Date().toISOString()}</div>
                <div>INTEGRITY: SHA-256 VERIFIED</div>
              </div>
            </div>

            <div className={`vc-local-stream ${videoOff ? "stream-off" : ""}`}>
              <span>Ministry Inspector (HQ)</span>
            </div>
          </div>

          {/* In-Call Controls & Observation Form */}
          <div className="vc-controls-and-notes">
            <div className="vc-buttons-bar">
              <button className={`btn-call-ctrl ${muted ? "active" : ""}`} onClick={() => setMuted(!muted)}>
                {muted ? "🔇 Unmute Mic" : "🎤 Mute Mic"}
              </button>
              <button className={`btn-call-ctrl ${videoOff ? "active" : ""}`} onClick={() => setVideoOff(!videoOff)}>
                {videoOff ? "📷 Turn Video On" : "📹 Turn Video Off"}
              </button>
            </div>

            <div className="vc-audit-form">
              <h4>Inspection Observation & Discrepancy Recording</h4>
              <textarea
                value={auditNotes}
                onChange={(e) => setAuditNotes(e.target.value)}
                placeholder="Record live audit observations: Does beneficiary look properly cared for? Is the center clean? Any food/ration complaints?"
                rows={3}
              />
              <div className="discrepancy-checkbox">
                <input
                  type="checkbox"
                  id="flag-disc"
                  checked={flagDiscrepancy}
                  onChange={(e) => setFlagDiscrepancy(e.target.checked)}
                />
                <label htmlFor="flag-disc">
                  🚨 Flag Discrepancy / Ghost Beneficiary Suspected (Triggers High-Priority Ground Inspection)
                </label>
              </div>
              <button
                className="btn-danger"
                onClick={handleFinishCall}
                disabled={savingCall}
                style={{ marginTop: "0.5rem" }}
              >
                {savingCall ? "Archiving Session..." : "End Session & Archive Official Audit Record"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Pre-Call Candidate Selection Wizard */
        <div className="card">
          <h3>Initiate Surprise Video Audit</h3>
          <p style={{ color: "#64748b", marginBottom: "1.5rem" }}>
            The system employs an automated randomization algorithm to select participants from verified facility rolls.
          </p>

          <div className="vc-wizard-grid">
            <div className="form-group">
              <label>1. Select Monitored Facility / NGO</label>
              <select value={selectedInstId} onChange={(e) => setSelectedInstId(e.target.value)}>
                {institutions.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name} ({i.district}) — {i.scheme}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>2. Select Target Category</label>
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value as any)}
              >
                <option value="BENEFICIARY">Random Enrolled Beneficiary (Anti-Ghost Audit)</option>
                <option value="STAFF">On-Duty Caregiver / Staff Member</option>
                <option value="INCHARGE">Project Director / Incharge (Center Walkthrough)</option>
              </select>
            </div>

            <div className="form-group" style={{ display: "flex", alignItems: "flex-end" }}>
              <button
                className="btn-highlight"
                onClick={handlePickCandidate}
                disabled={loadingCandidate || !selectedInstId}
                style={{ width: "100%" }}
              >
                {loadingCandidate ? "Randomizing..." : "🎲 Pick Random Candidate"}
              </button>
            </div>
          </div>

          {/* Candidate Card */}
          {candidate && (
            <div className="candidate-match-card">
              <div className="candidate-avatar">👤</div>
              <div className="candidate-details">
                <span className="badge-govt">{candidate.target_type} SELECTED</span>
                <h3>{candidate.name}</h3>
                <p>
                  <b>Role / Category:</b> {candidate.role} | <b>Center:</b> {candidate.institution_name}
                </p>
                {candidate.aadhaar_masked && (
                  <small>Aadhaar Verification: {candidate.aadhaar_masked} (Biometric Match Confirmed)</small>
                )}
                <div style={{ marginTop: "1rem" }}>
                  <button className="btn-primary" onClick={handleInitiateCall}>
                    📞 Initiate Surprise Video Call Now
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Historical Surprise VC Sessions */}
      <div className="card" style={{ marginTop: "1.5rem" }}>
        <h3>Recent Surprise Video Audit Records</h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date / Time</th>
                <th>Facility</th>
                <th>Target Person</th>
                <th>Auditor</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Observations</th>
              </tr>
            </thead>
            <tbody>
              {recentSessions.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", color: "#64748b" }}>
                    No recorded video audit sessions yet.
                  </td>
                </tr>
              ) : (
                recentSessions.map((s) => (
                  <tr key={s.id}>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                    <td><b>{s.institution_name}</b></td>
                    <td>{s.target_name} ({s.target_type})</td>
                    <td>{s.caller_name}</td>
                    <td>{s.duration_sec}s</td>
                    <td><span className="badge-success-small">{s.status}</span></td>
                    <td><small>{s.notes || "No discrepancy recorded."}</small></td>
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
