import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("admin@inspect-ai.local");
  const [password, setPassword] = useState("Admin@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLoginWith = async (e: string, p: string, targetPath: string) => {
    setError("");
    setLoading(true);
    try {
      await login(e, p);
      navigate(targetPath);
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-backdrop-glow"></div>

      <div className="login-modal-grid">
        {/* Left Hero Side */}
        <div className="login-hero-panel">
          <div className="hero-emblem-badge">
            <span className="emblem-crest">🏛️</span>
            <div>
              <span className="hero-govt-title">GOVERNMENT OF INDIA</span>
              <span className="hero-dept-title">Department of Social Justice & Empowerment</span>
            </div>
          </div>

          <div className="hero-heading-group">
            <h1 className="hero-title">INSPECT-AI</h1>
            <p className="hero-subtitle">
              Smart Real-Time Monitoring, Surveillance & AI-Driven Inspection Platform
            </p>
            <div className="hero-ps-pill">
              <span>PROBLEM STATEMENT ID: 26095</span>
              <span className="hero-theme-tag">SMART AUTOMATION</span>
            </div>
          </div>

          <div className="hero-feature-list">
            <div className="hero-feature-item">
              <span className="feature-icon">📹</span>
              <div>
                <b>Live CCTV Surveillance Grid</b>
                <small>24/7 visual monitoring across 4 mandatory center angles with AI crowd density</small>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">📞</span>
              <div>
                <b>Surprise Video Conferencing (VC)</b>
                <small>Unannounced on-demand walkthroughs with Project Incharges and Beneficiaries</small>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">🎲</span>
              <div>
                <b>AI Anti-Collusion Random Allocation</b>
                <small>Home district exclusion, 180-day cooling-off, and JIT sealed disclosure</small>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">🛰️</span>
              <div>
                <b>GPS Geo-Fenced Mobile App</b>
                <small>Field checklist unlocks only when verified &lt;100m from facility entrance</small>
              </div>
            </div>
          </div>

          <div className="hero-footer-bar">
            <span>🛡️ End-to-End Cryptographic Chain of Custody (SHA-256)</span>
          </div>
        </div>

        {/* Right Authentication Panel */}
        <div className="login-form-panel">
          <div className="form-panel-header">
            <h3>Portal Authentication</h3>
            <p>Sign in to access your designated stakeholder command environment</p>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-field">
              <label>Official Email Address</label>
              <div className="input-with-icon">
                <span className="input-icon">✉️</span>
                <input
                  type="email"
                  required
                  placeholder="admin@inspect-ai.local"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-field">
              <label>Secure Password</label>
              <div className="input-with-icon">
                <span className="input-icon">🔒</span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (
                <span>Validating Security Credentials...</span>
              ) : (
                <span>Sign In to System ➔</span>
              )}
            </button>
          </form>

          {/* Quick 1-Click Role Access Cards */}
          <div className="stakeholder-select-section">
            <div className="section-divider">
              <span>OR ONE-CLICK DEMO ACCESS</span>
            </div>

            <div className="role-cards-grid role-cards-grid-3">
              <button
                type="button"
                className="role-card-item ministry"
                onClick={() =>
                  handleLoginWith("admin@inspect-ai.local", "Admin@123", "/dashboard/central")
                }
              >
                <div className="role-card-top">
                  <span className="role-icon">🏛️</span>
                  <span className="role-tag-pill">Central Ministry</span>
                </div>
                <b>Dr. Meera Krishnan</b>
                <small>Joint Secretary, MoSJE Headquarters</small>
                <span className="role-action-hint">Enter Central Command ➔</span>
              </button>

              <button
                type="button"
                className="role-card-item ngo"
                onClick={() =>
                  handleLoginWith("ngo@inspect-ai.local", "Ngo@123", "/dashboard/ngo")
                }
              >
                <div className="role-card-top">
                  <span className="role-icon">🏢</span>
                  <span className="role-tag-pill">Aided NGO / Institute</span>
                </div>
                <b>S. Priya (Project Director)</b>
                <small>Mother Teresa Rehabilitation DDRS</small>
                <span className="role-action-hint">Enter Facility Portal ➔</span>
              </button>

              <button
                type="button"
                className="role-card-item inspector"
                onClick={() =>
                  handleLoginWith("inspector@inspect-ai.local", "Inspector@123", "/inspector-workbench")
                }
              >
                <div className="role-card-top">
                  <span className="role-icon">📝</span>
                  <span className="role-tag-pill">Field PMU Inspector</span>
                </div>
                <b>A. Kumar (Auditor)</b>
                <small>On-Site Inspection & Audit Workbench</small>
                <span className="role-action-hint">Open Field Workbench ➔</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
