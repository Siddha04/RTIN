import React, { useEffect, useState } from "react";
import { api, Evidence, Institution, Inspection } from "../api";

export const EvidencePage: React.FC = () => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Upload Form
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState("");
  const [instId, setInstId] = useState("");
  const [inspId, setInspId] = useState("");
  const [officerId, setOfficerId] = useState("USR-02");
  const [lat, setLat] = useState(11.6643);
  const [lng, setLng] = useState(78.1460);
  const [uploading, setUploading] = useState(false);
  const [verificationResult, setVerificationResult] = useState<Evidence | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [evData, instData, inspData] = await Promise.all([
        api.getEvidence(),
        api.getInstitutions(),
        api.getInspections()
      ]);
      setEvidenceList(evData);
      setInstitutions(instData);
      setInspections(inspData);

      if (instData.length > 0) setInstId(instData[0].id);
      if (inspData.length > 0) setInspId(inspData[0].id);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load evidence records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      // Compute SHA-256 hash in browser
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      setFileHash(hashHex);
    }
  };

  const handleUploadAndVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select a file to upload.");
      return;
    }
    setUploading(true);
    try {
      // 1. Upload to backend
      const uploadRes = await api.uploadEvidenceFile(selectedFile);

      // 2. Run verification API
      const verifyRes = await api.verifyEvidence({
        institution_id: instId,
        inspection_id: inspId,
        officer_id: officerId,
        latitude: lat,
        longitude: lng,
        captured_at: new Date().toISOString(),
        sha256_hash: uploadRes.sha256
      });

      setVerificationResult(verifyRes);
      setSelectedFile(null);
      setFileHash("");
      await loadData();
    } catch (err: any) {
      alert(`Evidence Verification Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="head">
        <div>
          <small>EVIDENCE INTEGRITY & VERIFICATION</small>
          <h1>Field Evidence Module</h1>
          <p>SHA-256 checksum verification, GPS location validation, and timestamp auditing.</p>
        </div>
      </div>

      <div className="grid">
        <article className="panel">
          <h2>Upload & Verify Evidence File</h2>
          <form onSubmit={handleUploadAndVerify}>
            <div className="form-group">
              <label>Select Evidence Image / Document</label>
              <input type="file" required onChange={handleFileChange} />
              {fileHash && (
                <small className="hash-display">Calculated Client SHA-256: <code>{fileHash}</code></small>
              )}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Institution</label>
                <select value={instId} onChange={(e) => setInstId(e.target.value)}>
                  {institutions.map((i) => (
                    <option key={i.id} value={i.id}>{i.name} ({i.id})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Associated Inspection</label>
                <select value={inspId} onChange={(e) => setInspId(e.target.value)}>
                  {inspections.map((i) => (
                    <option key={i.id} value={i.id}>{i.id} - {i.inspector}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Officer ID</label>
                <input
                  type="text"
                  required
                  value={officerId}
                  onChange={(e) => setOfficerId(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Captured GPS Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label>Captured GPS Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lng}
                  onChange={(e) => setLng(parseFloat(e.target.value))}
                />
              </div>
            </div>

            <button type="submit" className="primary-btn" disabled={uploading}>
              {uploading ? "Hashing & Verifying..." : "Upload & Run SHA-256 Verification"}
            </button>
          </form>

          {verificationResult && (
            <div className="verification-card" style={{ marginTop: "20px" }}>
              <h3>Verification Status: {verificationResult.verified ? "✅ PASSED" : "❌ FAILED"}</h3>
              <div className="check-grid">
                <div className={`check-item ${verificationResult.checks.gps ? "pass" : "fail"}`}>
                  GPS Check: {verificationResult.checks.gps ? "VALID" : "INVALID (0,0)"}
                </div>
                <div className={`check-item ${verificationResult.checks.timestamp ? "pass" : "fail"}`}>
                  Timestamp Check: {verificationResult.checks.timestamp ? "< 24 Hours" : "EXPIRED"}
                </div>
                <div className={`check-item ${verificationResult.checks.officer_id ? "pass" : "fail"}`}>
                  Officer ID Check: {verificationResult.checks.officer_id ? "PRESENT" : "MISSING"}
                </div>
                <div className={`check-item ${verificationResult.checks.sha256_integrity ? "pass" : "fail"}`}>
                  SHA-256 Check: {verificationResult.checks.sha256_integrity ? "MATCHED" : "CORRUPT"}
                </div>
              </div>
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Audit Log of Evidence Submissions</h2>
          {loading ? (
            <div className="loading-spinner">Loading evidence log...</div>
          ) : error ? (
            <div className="error-banner">{error}</div>
          ) : (
            <div className="table-rows">
              {evidenceList.map((ev) => (
                <div key={ev.id} className="row">
                  <div>
                    <b>{ev.file_name} ({ev.id})</b>
                    <small>Inspection: {ev.inspection_id} · Officer: {ev.officer_id}</small>
                    <code className="hash-code">{ev.sha256_hash.substring(0, 24)}...</code>
                  </div>
                  {ev.verified ? (
                    <em className="badge low">VERIFIED</em>
                  ) : (
                    <em className="badge high">FAILED</em>
                  )}
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </div>
  );
};
