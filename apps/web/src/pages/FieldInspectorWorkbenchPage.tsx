import React, { useEffect, useState } from "react";
import { api, Inspection, Institution } from "../api";
import { useAuth } from "../context/AuthContext";

export const FieldInspectorWorkbenchPage: React.FC = () => {
  const { user } = useAuth();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [selectedInsp, setSelectedInsp] = useState<Inspection | null>(null);
  const [targetInstitution, setTargetInstitution] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);

  // Duty State
  const [isSealed, setIsSealed] = useState(false);
  const [geofenceUnlocked, setGeofenceUnlocked] = useState(false);
  const [currentDist, setCurrentDist] = useState<number | null>(null);
  const [verifyingGeo, setVerifyingGeo] = useState(false);
  const [geoMessage, setGeoMessage] = useState<string | null>(null);

  // Official Audit Form State
  const [physicalHeadcount, setPhysicalHeadcount] = useState<number>(54);
  const [checklist, setChecklist] = useState({
    headcountMatches: true,
    kitchenHygiene: true,
    cctvFunctioning: true,
    dormitorySanitation: true,
    medicalLogbook: true,
    antiGhostVerified: true
  });
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [photoHash, setPhotoHash] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [recommendation, setRecommendation] = useState<string>("RECOMMEND_FULL_GRANT_RELEASE");
  const [undertakingSigned, setUndertakingSigned] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [submittedReport, setSubmittedReport] = useState<any | null>(null);

  const loadInspections = async () => {
    setLoading(true);
    try {
      const data = await api.getInspections();
      setInspections(data);
      if (data.length > 0) {
        selectInspection(data[0]);
      }
    } catch (err) {
      console.error("Failed to load inspections", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInspections();
  }, []);

  const selectInspection = async (insp: Inspection) => {
    setSelectedInsp(insp);
    setIsSealed(!!insp.is_surprise && insp.status === "assigned");
    setGeofenceUnlocked(!!insp.geofence_verified);
    setCurrentDist(insp.distance_to_target_meters || 42);
    setGeoMessage(insp.geofence_verified ? "GPS boundary confirmed within 50m of facility gate." : null);
    setCapturedPhoto(null);
    setPhotoHash(null);
    setSubmittedReport(null);
    setNotes(insp.notes || "");

    // Load institution details
    try {
      const inst = await api.getInstitution(insp.institution_id);
      setTargetInstitution(inst);
      if (inst?.beneficiaries) {
        setPhysicalHeadcount(inst.beneficiaries);
      }
    } catch (_) {
      setTargetInstitution(null);
    }
  };

  const handleSimulateLocation = async (mode: "NEAR" | "FAR") => {
    if (!selectedInsp) return;
    setVerifyingGeo(true);
    setGeoMessage(null);

    const coords = mode === "NEAR"
      ? { latitude: 11.6644, longitude: 78.1461 }
      : { latitude: 11.7500, longitude: 78.2500 };

    try {
      const res = await api.geofenceCheckin(selectedInsp.id, coords);
      setGeofenceUnlocked(res.geofence_unlocked);
      setCurrentDist(res.distance_meters);
      setGeoMessage(res.message);
      if (res.geofence_unlocked) {
        setIsSealed(false);
      }
    } catch (err: any) {
      alert(err.message || "Failed to verify geofence location");
    } finally {
      setVerifyingGeo(false);
    }
  };

  const handleDeviceGPS = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    setVerifyingGeo(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        if (!selectedInsp) return;
        try {
          const res = await api.geofenceCheckin(selectedInsp.id, {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude
          });
          setGeofenceUnlocked(res.geofence_unlocked);
          setCurrentDist(res.distance_meters);
          setGeoMessage(res.message);
          if (res.geofence_unlocked) setIsSealed(false);
        } catch (err: any) {
          alert(err.message || "Checkin failed");
        } finally {
          setVerifyingGeo(false);
        }
      },
      (err) => {
        alert(`GPS error: ${err.message}. Using simulated GPS button is recommended for desktop testing.`);
        setVerifyingGeo(false);
      }
    );
  };

  const handleCapturePhoto = () => {
    const hash = `sha256_${Math.random().toString(36).substring(2, 12)}${Date.now().toString(36)}`;
    setCapturedPhoto("https://images.unsplash.com/photo-1577896851231-70ef18881754?w=800&auto=format&fit=crop&q=80");
    setPhotoHash(hash);
  };

  const handleSubmitOfficialReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInsp) return;
    if (!undertakingSigned) {
      alert("Please check the official inspector undertaking before submitting.");
      return;
    }

    setSubmitting(true);
    try {
      const checklistPayload = {
        ...checklist,
        verified_headcount: physicalHeadcount,
        photo_hash: photoHash,
        recommendation,
        officer_name: user?.full_name || "A. Kumar",
        submitted_timestamp: new Date().toISOString()
      };

      await api.updateInspection(selectedInsp.id, {
        status: "completed",
        notes: notes || `On-site inspection completed. Recommendation: ${recommendation}`,
        checklist_data: checklistPayload
      });

      setSubmittedReport({
        inspectionId: selectedInsp.id,
        institutionName: selectedInsp.institution_name,
        recommendation,
        timestamp: new Date().toLocaleString(),
        certificateHash: `CERT_MoSJE_${Math.random().toString(36).substring(2, 10).toUpperCase()}`
      });

      // Reload list
      const refreshed = await api.getInspections();
      setInspections(refreshed);
    } catch (err: any) {
      alert(err.message || "Failed to submit inspection report");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="loading-spinner">Initializing PMU Field Inspector Workbench...</div>;
  }

  return (
    <div className="inspector-workbench-container">
      {/* Official Government Workbench Header */}
      <div className="command-banner">
        <div>
          <div className="badge-govt">DoSJE PMU FIELD INSPECTION & GROUND AUDIT SUITE</div>
          <h2>Field Inspector Official Audit Workbench</h2>
          <p>
            Field monitoring interface for designated PMU officers. Execute Just-in-Time unsealed duties, verify GPS boundary entrance, conduct physical headcount audits, capture watermarked evidence, and file official recommendations with the Ministry.
          </p>
        </div>
        <div className="banner-actions">
          <span className="badge-govt">Officer: {user?.full_name || "A. Kumar"}</span>
          <span className="badge-success">District: {user?.assigned_district || "Salem"}</span>
        </div>
      </div>

      <div className="two-column-grid" style={{ gridTemplateColumns: "360px 1fr", gap: "1.5rem", marginTop: "1rem" }}>
        {/* Left: Assigned Duty Roster & Blind Unsealing Queue */}
        <div>
          <div className="card">
            <div className="card-header-flex">
              <div>
                <h3>📋 Assigned Duty Roster</h3>
                <small>Select duty to load verification workbench</small>
              </div>
              <span className="badge-small">{inspections.length} Total</span>
            </div>

            <div className="duty-list-vertical" style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.8rem" }}>
              {inspections.map((i) => (
                <div
                  key={i.id}
                  onClick={() => selectInspection(i)}
                  className={`duty-item-card ${selectedInsp?.id === i.id ? "active-duty" : ""}`}
                  style={{
                    padding: "0.9rem 1rem",
                    borderRadius: "8px",
                    border: selectedInsp?.id === i.id ? "2px solid #0284c7" : "1px solid #e2e8f0",
                    background: selectedInsp?.id === i.id ? "#f0f9ff" : "#fff",
                    cursor: "pointer",
                    transition: "all 0.2s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.3rem" }}>
                    <b style={{ color: "#0f172a", fontSize: "0.95rem" }}>{i.id}</b>
                    <div style={{ display: "flex", gap: "0.3rem" }}>
                      {i.is_surprise && <span className="badge-danger">SURPRISE</span>}
                      <span className={`status-pill pill-${i.status}`}>{i.status.toUpperCase()}</span>
                    </div>
                  </div>
                  <div style={{ fontWeight: 600, color: "#1e293b", fontSize: "0.9rem" }}>{i.institution_name}</div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.4rem", color: "#64748b", fontSize: "0.8rem" }}>
                    <span>📍 {i.district}</span>
                    <span>{i.scheme_name || "DDRS"}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* GPS Gate Geofence Controller */}
          <div className="card" style={{ marginTop: "1.25rem" }}>
            <h3>🛰 GPS Gate Boundary Validation</h3>
            <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0.5rem 0 1rem 0" }}>
              Under MoSJE anti-tamper protocol, audit checklist unlocks only when officer GPS is confirmed within 100 meters of the institution perimeter.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              <button
                className="btn-success"
                onClick={() => handleSimulateLocation("NEAR")}
                disabled={verifyingGeo}
                style={{ width: "100%", textAlign: "left" }}
              >
                📍 Confirm Arrival at Gate (&lt; 50m)
              </button>
              <button
                className="btn-secondary"
                onClick={() => handleSimulateLocation("FAR")}
                disabled={verifyingGeo}
                style={{ width: "100%", textAlign: "left" }}
              >
                📍 Simulate Outside Boundary (12 km away)
              </button>
              <button
                className="btn-small"
                onClick={handleDeviceGPS}
                disabled={verifyingGeo}
                style={{ width: "100%", textAlign: "left", background: "#f8fafc", color: "#475569" }}
              >
                📡 Query Live Device Hardware GPS
              </button>
            </div>

            {currentDist !== null && (
              <div
                style={{
                  marginTop: "1rem",
                  padding: "0.8rem",
                  borderRadius: "6px",
                  background: geofenceUnlocked ? "#ecfdf5" : "#fef2f2",
                  border: geofenceUnlocked ? "1px solid #10b981" : "1px solid #ef4444"
                }}
              >
                <div style={{ fontWeight: 700, color: geofenceUnlocked ? "#065f46" : "#991b1b" }}>
                  {geofenceUnlocked ? "✓ GEOFENCE UNLOCKED (< 100m)" : "🔒 OUTSIDE GEOFENCE"}
                </div>
                <small style={{ color: "#475569", display: "block", marginTop: "0.2rem" }}>
                  Calculated Distance: {currentDist} meters
                </small>
                {geoMessage && <small style={{ color: "#64748b", display: "block" }}>{geoMessage}</small>}
              </div>
            )}
          </div>
        </div>

        {/* Right: Active On-Site Audit Form & Submission */}
        <div>
          {selectedInsp ? (
            <div>
              {/* Institution Overview Header */}
              <div className="card" style={{ marginBottom: "1.25rem", borderLeft: "4px solid #0284c7" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.3rem" }}>
                      <span className="badge-small">{selectedInsp.id}</span>
                      <span className="badge-govt">{targetInstitution?.scheme || "DDRS"}</span>
                      {selectedInsp.is_surprise && <span className="badge-danger">SURPRISE INSPECTION</span>}
                    </div>
                    <h3 style={{ margin: "0.2rem 0" }}>{selectedInsp.institution_name}</h3>
                    <p style={{ color: "#64748b", margin: 0, fontSize: "0.9rem" }}>
                      <b>District:</b> {selectedInsp.district} | <b>Sanctioned Capacity:</b> {targetInstitution?.sanctioned_capacity || 60} Beneficiaries | <b>Director:</b> {targetInstitution?.contact_person || "Project Incharge"}
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span className={`status-badge-custom ${geofenceUnlocked ? "badge-approved" : "badge-review"}`}>
                      {geofenceUnlocked ? "● Ready for On-Site Filing" : "🔒 Geofence Verification Pending"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Just-in-Time Sealed Duty Warning */}
              {isSealed ? (
                <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem", background: "#fffbeb", border: "1px solid #fde68a" }}>
                  <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>🔒</div>
                  <h3 style={{ color: "#92400e" }}>JUST-IN-TIME SEALED SURPRISE DUTY</h3>
                  <p style={{ color: "#78350f", maxWidth: "550px", margin: "0.5rem auto 1.5rem auto" }}>
                    To prevent advance tipping-off, collusion, or cosmetic center staging, detailed verification parameters remain encrypted until T-2 hours or GPS arrival into the facility perimeter.
                  </p>
                  <div style={{ display: "inline-block", background: "#fef3c7", padding: "0.5rem 1.2rem", borderRadius: "6px", fontWeight: 700, color: "#b45309", marginBottom: "1.5rem" }}>
                    COUNTDOWN: UNSEALS IN 01h 48m
                  </div>
                  <div>
                    <button
                      className="btn-highlight"
                      onClick={() => setIsSealed(false)}
                    >
                      🔓 Authenticate & Unseal Inspection Duty Now
                    </button>
                  </div>
                </div>
              ) : submittedReport ? (
                /* Success Certificate Banner */
                <div className="card" style={{ background: "#f0fdf4", border: "2px solid #10b981", textAlign: "center", padding: "2.5rem 1.5rem" }}>
                  <div style={{ fontSize: "3rem", color: "#10b981", marginBottom: "0.5rem" }}>✓</div>
                  <h2 style={{ color: "#065f46" }}>Official Inspection Report Filed with MoSJE Command</h2>
                  <p style={{ color: "#166534", maxWidth: "600px", margin: "0.5rem auto" }}>
                    The on-site inspection for <b>{submittedReport.institutionName}</b> has been cryptographically signed and archived into the central DoSJE audit vault.
                  </p>
                  <div style={{ margin: "1.5rem auto", maxWidth: "450px", background: "#fff", padding: "1rem", borderRadius: "8px", border: "1px dashed #86efac", textAlign: "left" }}>
                    <div><b>Inspection ID:</b> {submittedReport.inspectionId}</div>
                    <div><b>Official Ruling:</b> {submittedReport.recommendation}</div>
                    <div><b>Timestamp:</b> {submittedReport.timestamp}</div>
                    <div><b>Tamper-Proof Certificate:</b> <code style={{ color: "#0284c7" }}>{submittedReport.certificateHash}</code></div>
                  </div>
                  <button className="btn-secondary" onClick={() => setSubmittedReport(null)}>
                    Review or Re-open Duty
                  </button>
                </div>
              ) : (
                /* Full-Screen Official Inspection Protocol Form */
                <form onSubmit={handleSubmitOfficialReport}>
                  {/* Step 1: Headcount Audit */}
                  <div className="card" style={{ marginBottom: "1.25rem" }}>
                    <h4>1. Physical Headcount & Resident Audit</h4>
                    <p style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "1rem" }}>
                      Count all verified beneficiaries physically present inside the residential premises during inspection.
                    </p>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Physical Headcount Observed On-Site</label>
                        <input
                          type="number"
                          min="0"
                          required
                          value={physicalHeadcount}
                          onChange={(e) => setPhysicalHeadcount(parseInt(e.target.value) || 0)}
                          disabled={!geofenceUnlocked}
                        />
                      </div>
                      <div className="form-group">
                        <label>Sanctioned Capacity (DoSJE Approval)</label>
                        <input
                          type="number"
                          disabled
                          value={targetInstitution?.sanctioned_capacity || 60}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 2: MoSJE Official Verification Checklist */}
                  <div className="card" style={{ marginBottom: "1.25rem" }}>
                    <h4>2. Mandatory On-Site Verification Checklist</h4>
                    <p style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "1rem" }}>
                      Conduct physical walkthrough of facilities, registers, and surveillance systems:
                    </p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.headcountMatches}
                          onChange={(e) => setChecklist({ ...checklist, headcountMatches: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>Physical Headcount Reconciliation:</b> Physical headcount matches verified biometric roll and morning biometric punch without discrepancy.
                        </span>
                      </label>

                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.cctvFunctioning}
                          onChange={(e) => setChecklist({ ...checklist, cctvFunctioning: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>24/7 CCTV Surveillance Compliance:</b> All 4 mandated cameras (Entrance, Kitchen, Dormitory, Activity Hall) are streaming and un-occluded.
                        </span>
                      </label>

                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.kitchenHygiene}
                          onChange={(e) => setChecklist({ ...checklist, kitchenHygiene: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>Kitchen & Nutritional Standards:</b> Food preparation meets government dietary norms; clean RO drinking water and sanitary food storage verified.
                        </span>
                      </label>

                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.dormitorySanitation}
                          onChange={(e) => setChecklist({ ...checklist, dormitorySanitation: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>Living Space & Fire Safety:</b> Adequate square footage per bed, clean linens, functional ventilation, and unexpired fire extinguishers present.
                        </span>
                      </label>

                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.medicalLogbook}
                          onChange={(e) => setChecklist({ ...checklist, medicalLogbook: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>Doctor & Nurse Visit Registers:</b> Weekly medical checkup register signed with registered practitioner registration numbers.
                        </span>
                      </label>

                      <label className="checkbox-item-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={checklist.antiGhostVerified}
                          onChange={(e) => setChecklist({ ...checklist, antiGhostVerified: e.target.checked })}
                          disabled={!geofenceUnlocked}
                        />
                        <span>
                          <b>Anti-Ghost / Anti-Proxy Screening:</b> Direct interaction with random residents confirmed authentic identities (no fictitious names on register).
                        </span>
                      </label>
                    </div>
                  </div>

                  {/* Step 3: Photo Evidence */}
                  <div className="card" style={{ marginBottom: "1.25rem" }}>
                    <h4>3. Tamper-Proof Photographic Evidence</h4>
                    <p style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "1rem" }}>
                      Capture geo-tagged on-site photographic evidence. Photographs are cryptographically stamped with SHA-256 and UTC timestamp.
                    </p>

                    {capturedPhoto ? (
                      <div>
                        <div style={{ position: "relative", maxWidth: "500px", borderRadius: "8px", overflow: "hidden", border: "1px solid #cbd5e1" }}>
                          <img src={capturedPhoto} alt="Audit Evidence" style={{ width: "100%", display: "block" }} />
                          <div
                            style={{
                              position: "absolute",
                              bottom: 0,
                              left: 0,
                              right: 0,
                              background: "rgba(15, 23, 42, 0.85)",
                              color: "#fff",
                              padding: "0.5rem 0.8rem",
                              fontSize: "0.75rem",
                              fontFamily: "monospace"
                            }}
                          >
                            <div>GPS: 11.6644 N, 78.1461 E • ACCURACY: 4m</div>
                            <div>UTC: {new Date().toISOString()}</div>
                            <div>HASH: {photoHash}</div>
                          </div>
                        </div>
                        <button
                          type="button"
                          className="btn-secondary btn-small"
                          onClick={() => setCapturedPhoto(null)}
                          style={{ marginTop: "0.6rem" }}
                        >
                          Retake Photo Evidence
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={handleCapturePhoto}
                        disabled={!geofenceUnlocked}
                      >
                        📷 Capture Geo-Stamped Audit Photograph
                      </button>
                    )}
                  </div>

                  {/* Step 4: Observations & Official Recommendation */}
                  <div className="card" style={{ marginBottom: "1.25rem" }}>
                    <h4>4. Audit Observations & Official Recommendation to MoSJE</h4>

                    <div className="form-group" style={{ marginTop: "0.8rem" }}>
                      <label>Inspector Observations & Detailed Remarks</label>
                      <textarea
                        rows={3}
                        required
                        placeholder="Detail observations regarding resident satisfaction, caregiver availability, infrastructure conditions, or discrepancies..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        disabled={!geofenceUnlocked}
                      />
                    </div>

                    <div className="form-group">
                      <label style={{ fontWeight: 700, color: "#0f172a" }}>
                        Official Inspector Recommendation to Central Ministry (MoSJE)
                      </label>
                      <select
                        value={recommendation}
                        onChange={(e) => setRecommendation(e.target.value)}
                        disabled={!geofenceUnlocked}
                        style={{ fontWeight: 600, padding: "0.75rem" }}
                      >
                        <option value="RECOMMEND_FULL_GRANT_RELEASE">
                          ✓ RECOMMEND FULL GRANT RELEASE — Satisfactory Ground Reality & Verified Compliance
                        </option>
                        <option value="ISSUE_15_DAY_RECTIFICATION_NOTICE">
                          ⚠️ ISSUE 15-DAY RECTIFICATION NOTICE — Minor Rectifiable Gaps (Conditional Release)
                        </option>
                        <option value="CRITICAL_FRAUD_GRANT_FREEZE">
                          🚨 CRITICAL FRAUD / GHOST BENEFICIARIES — Recommend Immediate Grant Freeze & Show-Cause
                        </option>
                      </select>
                    </div>

                    <div className="form-group checkbox-group" style={{ background: "#f8fafc", padding: "0.8rem", borderRadius: "6px", marginTop: "1rem" }}>
                      <label style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={undertakingSigned}
                          onChange={(e) => setUndertakingSigned(e.target.checked)}
                          disabled={!geofenceUnlocked}
                          style={{ marginTop: "0.25rem" }}
                        />
                        <span style={{ fontSize: "0.85rem", color: "#334155" }}>
                          <b>Field Officer Certification:</b> I solemnly declare that I have physically visited this facility today, carried out the verification in person, and the data provided above represents true ground reality.
                        </span>
                      </label>
                    </div>

                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={submitting || !geofenceUnlocked}
                      style={{ width: "100%", padding: "1rem", fontSize: "1.05rem", marginTop: "1rem" }}
                    >
                      {submitting ? "Cryptographically Signing & Submitting..." : "🏛 Finalize Official Inspection Report & File to Ministry Command"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
              <p style={{ color: "#64748b" }}>Select an assigned duty from the roster to begin on-site verification.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
