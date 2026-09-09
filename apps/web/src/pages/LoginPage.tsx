import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSelect = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>INSPECT-AI</h1>
          <p>Smart Real-Time Monitoring & Inspection Command Center</p>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              required
              placeholder="admin@inspect-ai.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? "Authenticating..." : "Sign In to Command Center"}
          </button>
        </form>

        <div className="demo-accounts">
          <small>QUICK DEMO ACCOUNTS</small>
          <div className="demo-btn-group">
            <button type="button" onClick={() => handleDemoSelect("admin@inspect-ai.local", "Admin@123")}>
              Ministry Admin
            </button>
            <button type="button" onClick={() => handleDemoSelect("inspector@inspect-ai.local", "Inspector@123")}>
              Field Inspector
            </button>
            <button type="button" onClick={() => handleDemoSelect("ngo@inspect-ai.local", "Ngo@123")}>
              NGO Partner
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
