import React, { useEffect, useState } from "react";
import { api, CCTVFeed } from "../api";

export const CCTVPage: React.FC = () => {
  const [feeds, setFeeds] = useState<CCTVFeed[]>([]);
  const [selectedScheme, setSelectedScheme] = useState("All");
  const [selectedFeed, setSelectedFeed] = useState<CCTVFeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [snapshotMsg, setSnapshotMsg] = useState<string | null>(null);
  const [capturing, setCapturing] = useState(false);

  const loadFeeds = async () => {
    setLoading(true);
    try {
      const data = await api.getCctvFeeds({
        scheme: selectedScheme !== "All" ? selectedScheme : undefined
      });
      setFeeds(data);
      if (data.length > 0 && !selectedFeed) {
        setSelectedFeed(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeeds();
  }, [selectedScheme]);

  const handleCaptureSnapshot = async () => {
    if (!selectedFeed) return;
    setCapturing(true);
    setSnapshotMsg(null);
    try {
      const res = await api.captureCctvSnapshot(selectedFeed.id);
      setSnapshotMsg(
        `✓ Evidence Snapshot Captured & Cryptographically Hashed! Evidence ID: ${res.evidence_id} | SHA-256: ${res.sha256_hash.substring(0, 16)}...`
      );
    } catch (err: any) {
      alert(err.message || "Failed to capture snapshot");
    } finally {
      setCapturing(false);
    }
  };

  return (
    <div className="cctv-hub-container">
      <div className="command-banner">
        <div>
          <div className="badge-govt">CENTRAL SURVEILLANCE & CCTV MONITORING HUB</div>
          <h2>Live Institutional CCTV Video Feeds (24/7 Monitoring)</h2>
          <p>
            Real-time visual monitoring of aided centers under DoSJE schemes. Detects ghost occupancy, monitors hygiene in kitchens, and verifies residential attendance.
          </p>
        </div>
      </div>

      {/* Scheme Filter Toolbar */}
      <div className="cctv-filter-toolbar">
        <div className="cctv-filter-heading">
          <span className="filter-label">SCHEME SELECTION:</span>
        </div>
        <div className="scheme-pill-list">
          {[
            { id: "All", label: "🌐 All Schemes" },
            { id: "DDRS", label: "♿ DDRS (Divyangjan)" },
            { id: "SENIOR_CITIZENS", label: "👴 Senior Citizens" },
            { id: "SMILE", label: "🌈 SMILE" },
            { id: "NMBA", label: "🌿 Nasha Mukti" },
            { id: "PM_AJAY", label: "📚 PM-AJAY" }
          ].map((s) => (
            <button
              key={s.id}
              type="button"
              className={`scheme-filter-pill ${selectedScheme === s.id ? "active" : ""}`}
              onClick={() => setSelectedScheme(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="filter-stats-badge">
          <span className="active-dot">●</span> <b>{feeds.length}</b> Active Feeds (AES-256)
        </div>
      </div>

      {snapshotMsg && <div className="success-banner">{snapshotMsg}</div>}

      {/* Main Video Theatre & Camera Switcher */}
      {selectedFeed && (
        <div className="card cctv-theatre-card" style={{ marginBottom: "1.5rem" }}>
          <div className="card-header-flex">
            <div>
              <h3>
                📹 {selectedFeed.institution_name} — {selectedFeed.camera_name}
              </h3>
              <small>
                {selectedFeed.district} | Scheme: {selectedFeed.scheme} | Stream ID: {selectedFeed.id}
              </small>
            </div>
            <button
              className="btn-highlight"
              onClick={handleCaptureSnapshot}
              disabled={capturing}
            >
              {capturing ? "Hashing Snapshot..." : "📸 Capture Evidence Snapshot"}
            </button>
          </div>

          <div className="cctv-theatre-player">
            <video
              src={selectedFeed.stream_url}
              autoPlay
              loop
              muted
              playsInline
              className="cctv-main-video"
            />
            {/* AI HUD Overlay */}
            <div className="cctv-hud-overlay">
              <div className="hud-top-bar">
                <span className="hud-live-tag">● LIVE TRANSMISSION</span>
                <span className="hud-timestamp">{new Date().toLocaleString()} UTC</span>
              </div>
              <div className="hud-bottom-bar">
                <div className="hud-ai-count">
                  <span className="hud-metric-label">AI CROWD ESTIMATION</span>
                  <b className="hud-metric-value">{selectedFeed.ai_crowd_count} PERSONS DETECTED</b>
                </div>
                <div className="hud-integrity">
                  <span>SHA-256 HASH CHAIN: ACTIVE</span>
                  <span>ENCRYPTION: AES-256-GCM</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* All Camera Feeds Grid */}
      <div className="card">
        <h3>Institutional Surveillance Camera Grid</h3>
        <p style={{ color: "#64748b", marginBottom: "1rem" }}>
          Click any camera below to load its high-definition live stream into the command theatre.
        </p>

        {loading ? (
          <div className="loading-spinner">Connecting to Video Feeds...</div>
        ) : (
          <div className="cctv-grid-large">
            {feeds.map((f) => (
              <div
                key={f.id}
                className={`cctv-grid-box ${selectedFeed?.id === f.id ? "active-feed" : ""}`}
                onClick={() => setSelectedFeed(f)}
              >
                <div className="cctv-thumb-container">
                  <video src={f.stream_url} muted loop autoPlay className="cctv-thumb-video" />
                  <div className="cctv-thumb-badge">● {f.camera_name}</div>
                  <div className="cctv-thumb-count">{f.ai_crowd_count} Present</div>
                </div>
                <div className="cctv-thumb-footer">
                  <b>{f.institution_name}</b>
                  <div className="cctv-thumb-meta">
                    <small>{f.district} • {f.scheme}</small>
                    <span className={`status-dot ${f.status === "ONLINE" ? "green" : "red"}`}>
                      {f.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
