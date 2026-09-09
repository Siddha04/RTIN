import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passSuccess, setPassSuccess] = useState("");
  const [passError, setPassError] = useState("");
  const [submittingPass, setSubmittingPass] = useState(false);

  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [backendTime, setBackendTime] = useState<string>("");

  useEffect(() => {
    fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/health")
      .then((r) => r.json())
      .then((data) => {
        setBackendStatus("ONLINE (200 OK)");
        setBackendTime(data.time);
      })
      .catch(() => {
        setBackendStatus("OFFLINE / UNREACHABLE");
      });
  }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassError("");
    setPassSuccess("");
    setSubmittingPass(true);

    try {
      await api.changePassword({ old_password: oldPassword, new_password: newPassword });
      setPassSuccess("Password updated successfully!");
      setOldPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPassError(err.message || "Failed to update password");
    } finally {
      setSubmittingPass(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div>
      <div className="head">
        <div>
          <small>SYSTEM & USER CONFIGURATION</small>
          <h1>Account & System Settings</h1>
          <p>Manage user security, password credentials, and system connectivity.</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          Sign Out of Account
        </button>
      </div>

      <div className="grid">
        <article className="panel">
          <h2>User Profile Details</h2>
          <div className="detail-meta">
            <div className="meta-item">
              <label>Full Name:</label>
              <span>{user?.full_name}</span>
            </div>
            <div className="meta-item">
              <label>Email Address:</label>
              <span>{user?.email}</span>
            </div>
            <div className="meta-item">
              <label>Assigned System Role:</label>
              <em className="badge medium">{user?.role?.toUpperCase()} ADMIN</em>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Backend Service Connectivity</h2>
          <div className="detail-meta">
            <div className="meta-item">
              <label>FastAPI Engine Status:</label>
              <strong style={{ color: backendStatus.includes("ONLINE") ? "#37a66a" : "#d65a4c" }}>
                {backendStatus}
              </strong>
            </div>
            <div className="meta-item">
              <label>API Gateway Endpoint:</label>
              <code>{import.meta.env.VITE_API_URL || "http://localhost:8000"}</code>
            </div>
            <div className="meta-item">
              <label>Server UTC Timestamp:</label>
              <small>{backendTime || "N/A"}</small>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Update Password</h2>
          {passSuccess && <div className="success-banner" style={{ background: "#e7f6ed", color: "#177b4a", padding: "10px", borderRadius: "8px", marginBottom: "10px" }}>{passSuccess}</div>}
          {passError && <div className="error-banner">{passError}</div>}
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                required
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="primary-btn" disabled={submittingPass}>
              {submittingPass ? "Updating..." : "Update Password"}
            </button>
          </form>
        </article>
      </div>
    </div>
  );
};
