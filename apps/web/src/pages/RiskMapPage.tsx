import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api, Institution } from "../api";

export const RiskMapPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterBand, setFilterBand] = useState<string>("ALL");
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const navigate = useNavigate();

  const loadMapData = async () => {
    try {
      const data = await api.getInstitutions();
      setInstitutions(data);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load map points");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMapData();
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current || loading) return;

    if (!mapInstanceRef.current) {
      // Initialize Leaflet Map centered over Tamil Nadu region
      const map = L.map(mapContainerRef.current).setView([11.3, 77.8], 8);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
      }).addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Filter points
    const filtered = filterBand === "ALL"
      ? institutions
      : institutions.filter((i) => i.risk_band === filterBand);

    filtered.forEach((inst) => {
      const color = inst.risk_band === "HIGH" ? "#d65a4c" : inst.risk_band === "MEDIUM" ? "#dba43e" : "#37a66a";

      const customIcon = L.divIcon({
        className: "custom-map-pin",
        html: `<div style="background-color:${color}; width:24px; height:24px; border-radius:50%; border:3px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; color:#fff; font-size:10px; font-weight:bold;">${inst.risk_score}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([inst.lat, inst.lng], { icon: customIcon }).addTo(map);

      const popupContent = document.createElement("div");
      popupContent.className = "map-popup";
      popupContent.innerHTML = `
        <b style="font-size:14px; display:block; color:#0c3558;">${inst.name}</b>
        <small style="color:#666;">${inst.id} · ${inst.district}</small>
        <hr style="margin:6px 0; border:0; border-top:1px solid #eee;" />
        <div style="font-size:12px; margin-bottom:4px;">
          <b>Risk Score:</b> ${inst.risk_score} <span style="background:${color}; color:#fff; padding:2px 6px; border-radius:10px; font-size:10px;">${inst.risk_band}</span>
        </div>
        <div style="font-size:11px; color:#444;">
          Attendance: ${inst.attendance}% | Beneficiaries: ${inst.beneficiaries}
        </div>
        <div style="font-size:11px; margin-top:4px; color:#0e7f7a;">
          <b>Action:</b> ${inst.recommendation}
        </div>
      `;

      const viewBtn = document.createElement("button");
      viewBtn.className = "primary-btn";
      viewBtn.style.fontSize = "11px";
      viewBtn.style.padding = "4px 8px";
      viewBtn.style.marginTop = "8px";
      viewBtn.textContent = "View Profile →";
      viewBtn.onclick = () => navigate(`/institutions/${inst.id}`);

      popupContent.appendChild(viewBtn);

      marker.bindPopup(popupContent);
      markersRef.current.push(marker);
    });
  }, [institutions, filterBand, loading, navigate]);

  return (
    <div>
      <div className="head">
        <div>
          <small>GEOSPATIAL INTELLIGENCE</small>
          <h1>State Risk Map</h1>
          <p>Interactive location map of registered institutions categorized by AI risk score.</p>
        </div>
        <div className="button-group">
          <button className={`secondary-btn ${filterBand === "ALL" ? "active" : ""}`} onClick={() => setFilterBand("ALL")}>
            All ({institutions.length})
          </button>
          <button className={`secondary-btn ${filterBand === "HIGH" ? "active" : ""}`} onClick={() => setFilterBand("HIGH")}>
            High Risk ({institutions.filter((i) => i.risk_band === "HIGH").length})
          </button>
          <button className={`secondary-btn ${filterBand === "MEDIUM" ? "active" : ""}`} onClick={() => setFilterBand("MEDIUM")}>
            Medium Risk ({institutions.filter((i) => i.risk_band === "MEDIUM").length})
          </button>
          <button className={`secondary-btn ${filterBand === "LOW" ? "active" : ""}`} onClick={() => setFilterBand("LOW")}>
            Low Risk ({institutions.filter((i) => i.risk_band === "LOW").length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner">Initializing OpenStreetMap geospatial layer...</div>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : (
        <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
          <div ref={mapContainerRef} style={{ width: "100%", height: "550px" }} />
        </div>
      )}
    </div>
  );
};
