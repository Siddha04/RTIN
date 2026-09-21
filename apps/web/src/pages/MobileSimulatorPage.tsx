import React, { useEffect, useState } from "react";
import { api, Inspection } from "../api";

export const MobileSimulatorPage: React.FC = () => {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [selectedInsp, setSelectedInsp] = useState<Inspection | null>(null);
  const [isSealed, setIsSealed] = useState(false);
  const [geofenceUnlocked, setGeofenceUnlocked] = useState(false);
  const [currentDist, setCurrentDist] = useState<number | null>(null);
  const [verifyingGeo, setVerifyingGeo] = useState(false);
  const [geoMessage, setGeoMessage] = useState<string | null>(null);

  // Evidence capture state
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [photoHash, setPhotoHash] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [submittedSuccess, setSubmittedSuccess] = useState(false);

  // Offline queue state
  const [isOffline, setIsOffline] = useState(false);
  const [offlineQueue, setOfflineQueue] = useState<any[]>([]);

  useEffect(() => {
    api.getInspections().then((data) => {
      setInspections(data);
      if (data.length > 0) {
        selectInspection(data[0]);
      }
    });
  }, []);

  const selectInspection = (insp: Inspection) => {
    setSelectedInsp(insp);
    setIsSealed(!!insp.is_surprise && insp.status === "assigned");
    setGeofenceUnlocked(!!insp.geofence_verified);
    setCurrentDist(insp.distance_to_target_meters || null);
    setGeoMessage(null);
    setCapturedPhoto(null);
    setSubmittedSuccess(false);
  };

  const simulateLocation = async (type: "FAR" | "NEAR") => {
    if (!selectedInsp) return;
    setVerifyingGeo(true);
    setGeoMessage(null);

    // Target is approx lat 11.6643, lng 78.1460
    const coords = type === "NEAR"
      ? { latitude: 11.6644, longitude: 78.1461 }  // ~35m away
      : { latitude: 11.7500, longitude: 78.2500 }; // ~14 km away

    try {
      const res = await api.geofenceCheckin(selectedInsp.id, coords);
      setGeofenceUnlocked(res.geofence_unlocked);
      setCurrentDist(res.distance_meters);
      setGeoMessage(res.message);
      if (res.geofence_unlocked) {
        setIsSealed(false); // Unsealed upon reaching location
      }
    } catch (err: any) {
      alert(err.message || "Failed to checkin");
    } finally {
      setVerifyingGeo(false);
    }
  };

  const simulatePhotoCapture = () => {
    const sampleHash = `sha256_${Math.random().toString(36).substring(2, 10)}${Date.now().toString(36)}`;
    setCapturedPhoto("https://images.unsplash.com/photo-1577896851231-70ef18881754?w=600&auto=format&fit=crop&q=80");
    setPhotoHash(sampleHash);
  };

  const handleSubmitAudit = async () => {
    if (!selectedInsp) return;

    const payload = {
      inspection_id: selectedInsp.id,
      notes,
      photo_hash: photoHash,
      timestamp: new Date().toISOString()
    };

    if (isOffline) {
      setOfflineQueue((prev) => [...prev, payload]);
      setSubmittedSuccess(true);
      alert("Offline Mode Active: Inspection securely stored in local encrypted queue. Will auto-sync when connection restores.");
      return;
    }

    try {
      await api.updateInspection(selectedInsp.id, {
        status: "completed",
        notes: notes || "Mobile field inspection verified on-site with GPS & SHA-256 evidence."
      });
      setSubmittedSuccess(true);
    } catch (err: any) {
      alert(err.message || "Failed to submit");
    }
  };

  const syncOfflineQueue = async () => {
    for (const item of offlineQueue) {
      await api.updateInspection(item.inspection_id, {
        status: "completed",
        notes: item.notes
      });
    }
    setOfflineQueue([]);
    alert("✓ All offline inspection records successfully synchronized with Ministry Central Server!");
  };

  return (
    <div className="mobile-simulator-page">
      <div className="command-banner">
        <div>
          <div className="badge-govt">FIELD INSPECTION MOBILE APPLICATION SUITE</div>
          <h2>Field Inspector & PMU Mobile App Simulator</h2>
          <p>
            An interactive simulator demonstrating the dedicated field mobile tool: GPS geo-fencing validation (&lt; 100m unlock), Just-in-Time sealed duty countdown, tamper-proof watermarked camera, and offline sync.
          </p>
        </div>
      </div>

      <div className="simulator-workbench">
        {/* Inspection Selector Controls on Left */}
        <div className="simulator-controls-panel">
          <div className="card">
            <h3>Select Inspection Duty</h3>
            <p style={{ color: "#64748b", marginBottom: "1rem" }}>
              Choose a scheduled or surprise assignment to test mobile field behavior:
            </p>

            <div className="inspection-selector-list">
              {inspections.map((i) => (
                <div
                  key={i.id}
                  className={`selector-item ${selectedInsp?.id === i.id ? "active" : ""}`}
                  onClick={() => selectInspection(i)}
                >
                  <div className="selector-title-row">
                    <b>{i.id}</b>
                    {i.is_surprise && <span className="badge-danger">SURPRISE</span>}
                  </div>
                  <div>{i.institution_name}</div>
                  <small>{i.district} • Status: {i.status}</small>
                </div>
              ))}
            </div>
          </div>

          {/* Geo-Location Testing Tool */}
          <div className="card" style={{ marginTop: "1rem" }}>
            <h3>🛰 GPS Geo-Fence Simulation</h3>
            <p style={{ color: "#64748b", marginBottom: "1rem" }}>
              Test boundary verification. The inspection checklist is <b>locked</b> until inspector GPS is confirmed within 100m:
            </p>

            <div className="geo-buttons-grid">
              <button
                className="btn-danger"
                onClick={() => simulateLocation("FAR")}
                disabled={verifyingGeo}
              >
                📍 Simulate Far Away (14 km away)
              </button>
              <button
                className="btn-success"
                onClick={() => simulateLocation("NEAR")}
                disabled={verifyingGeo}
              >
                📍 Simulate On-Site (&lt; 100m from Gate)
              </button>
            </div>

            {currentDist !== null && (
              <div className="geo-result-box" style={{ marginTop: "1rem" }}>
                <b>Current Calculated Distance: {currentDist} meters</b>
                <p>{geoMessage}</p>
              </div>
            )}
          </div>

          {/* Network Simulator */}
          <div className="card" style={{ marginTop: "1rem" }}>
            <h3>📶 Network Connectivity Simulator</h3>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <b>{isOffline ? "🔴 Cellular Offline (No Network)" : "🟢 4G/5G Online"}</b>
                <small style={{ display: "block", color: "#64748b" }}>
                  Offline Queue: {offlineQueue.length} pending records
                </small>
              </div>
              <button
                className={`btn-small ${isOffline ? "btn-success" : "btn-secondary"}`}
                onClick={() => {
                  if (isOffline && offlineQueue.length > 0) {
                    syncOfflineQueue();
                  }
                  setIsOffline(!isOffline);
                }}
              >
                {isOffline ? "Restore Connection & Auto-Sync" : "Simulate Signal Drop (Offline)"}
              </button>
            </div>
          </div>
        </div>

        {/* Smartphone Device Frame */}
        <div className="smartphone-wrapper">
          <div className="smartphone-chassis">
            <div className="phone-notch">
              <div className="phone-speaker" />
              <div className="phone-cam" />
            </div>

            {/* Phone Screen Content */}
            <div className="phone-screen">
              {/* Status Bar */}
              <div className="phone-status-bar">
                <span>09:41</span>
                <span>📶 5G  •  🔋 94%</span>
              </div>

              {/* Mobile App Header */}
              <div className="mobile-app-header">
                <b>INSPECT-AI FIELD</b>
                <span className="mobile-role-tag">OFFICER: A. KUMAR</span>
              </div>

              {/* Mobile Body */}
              <div className="mobile-app-body">
                {selectedInsp ? (
                  <div>
                    {/* Sealed Duty Card */}
                    {isSealed ? (
                      <div className="mobile-sealed-card">
                        <div className="envelope-icon">🔒</div>
                        <h3>JUST-IN-TIME SEALED DUTY</h3>
                        <p>Surprise Audit Target Location</p>
                        <div className="sealed-countdown">UNSEALS IN: 01h 48m</div>
                        <small>
                          To prevent advance tipping-off and collusion, destination is sealed until T-2 hours or GPS entry into district.
                        </small>
                        <button
                          className="btn-small"
                          style={{ marginTop: "1rem", background: "#f59e0b", color: "#000" }}
                          onClick={() => setIsSealed(false)}
                        >
                          Manual HQ Override (Unseal Now)
                        </button>
                      </div>
                    ) : (
                      <div>
                        {/* Target Info */}
                        <div className="mobile-duty-header">
                          <span className="badge-small">{selectedInsp.id}</span>
                          <h4>{selectedInsp.institution_name}</h4>
                          <small>{selectedInsp.district} • {selectedInsp.scheme_name || "DDRS Scheme"}</small>
                        </div>

                        {/* Geo-Fence Status Banner */}
                        <div className={`mobile-geofence-banner ${geofenceUnlocked ? "unlocked" : "locked"}`}>
                          {geofenceUnlocked ? (
                            <div>✓ GPS VERIFIED ON-SITE (&lt; 100m) • AUDIT UNLOCKED</div>
                          ) : (
                            <div>🔒 OUTSIDE GEOFENCE • CHECKLIST LOCKED</div>
                          )}
                        </div>

                        {/* Checklist (Disabled if locked) */}
                        <div className={`mobile-checklist-box ${!geofenceUnlocked ? "disabled-checklist" : ""}`}>
                          <h5>Official Verification Checklist</h5>
                          <label className="mobile-check-item">
                            <input type="checkbox" defaultChecked={geofenceUnlocked} disabled={!geofenceUnlocked} />
                            <span>Physical Headcount matches Register</span>
                          </label>
                          <label className="mobile-check-item">
                            <input type="checkbox" defaultChecked={geofenceUnlocked} disabled={!geofenceUnlocked} />
                            <span>Kitchen & Nutrition Norms Met</span>
                          </label>
                          <label className="mobile-check-item">
                            <input type="checkbox" defaultChecked={geofenceUnlocked} disabled={!geofenceUnlocked} />
                            <span>CCTV 4-Camera System Functioning</span>
                          </label>
                          <label className="mobile-check-item">
                            <input type="checkbox" defaultChecked={geofenceUnlocked} disabled={!geofenceUnlocked} />
                            <span>No Proxy or Ghost Beneficiaries Found</span>
                          </label>
                        </div>

                        {/* Evidence Camera */}
                        <div className="mobile-evidence-section" style={{ marginTop: "1rem" }}>
                          <h5>Tamper-Proof Photo Evidence</h5>
                          {capturedPhoto ? (
                            <div className="mobile-photo-preview">
                              <img src={capturedPhoto} alt="Audit" />
                              <div className="photo-watermark-overlay">
                                <div>GPS: 11.6643 N, 78.1460 E</div>
                                <div>UTC: {new Date().toISOString()}</div>
                                <div>SHA-256: {photoHash?.substring(0, 16)}...</div>
                              </div>
                            </div>
                          ) : (
                            <button
                              className="btn-secondary mobile-cam-btn"
                              onClick={simulatePhotoCapture}
                              disabled={!geofenceUnlocked}
                            >
                              📷 Capture Geo-Stamped Audit Photo
                            </button>
                          )}
                        </div>

                        {/* Audit Notes */}
                        <div style={{ marginTop: "1rem" }}>
                          <textarea
                            className="mobile-textarea"
                            placeholder="Officer Observations & Remarks..."
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            disabled={!geofenceUnlocked}
                            rows={2}
                          />
                        </div>

                        {/* Submit Button */}
                        <div style={{ marginTop: "1rem" }}>
                          {submittedSuccess ? (
                            <div className="badge-success" style={{ textAlign: "center", padding: "0.8rem", width: "100%" }}>
                              ✓ Audit Record Successfully Logged
                            </div>
                          ) : (
                            <button
                              className="btn-primary mobile-submit-btn"
                              onClick={handleSubmitAudit}
                              disabled={!geofenceUnlocked}
                            >
                              {isOffline ? "💾 Save to Encrypted Offline Queue" : "✓ Finalize & Submit Audit"}
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p>No duty selected.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
