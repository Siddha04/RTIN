import React from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const Layout: React.FC = () => {
  const { user, logout, switchRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleRoleSwitch = async (role: "ministry" | "ngo" | "inspector") => {
    await switchRole(role);
    if (role === "ministry") navigate("/dashboard/central");
    else if (role === "ngo") navigate("/dashboard/ngo");
    else if (role === "inspector") navigate("/inspector-workbench");
  };

  const role = user?.role || "ministry";

  return (
    <div className="app-shell">
      {/* Top Header */}
      <header>
        <div className="brand">
          <div className="brand-crest-row">
            <span className="brand-crest">🏛️</span>
            <div>
              <b>INSPECT-AI</b>
              <small>
                {role === "ministry" && "Central Ministry Command (MoSJE)"}
                {role === "ngo" && "Aided Institution Facility Portal"}
                {role === "inspector" && "PMU Field Inspector Mobile Console"}
              </small>
            </div>
          </div>
        </div>

        {/* Interactive Quick Role Switcher Bar */}
        <div className="role-switcher-bar">
          <span className="switcher-label">DEMO ROLE:</span>
          <button
            className={`role-tab ${role === "ministry" ? "active" : ""}`}
            onClick={() => handleRoleSwitch("ministry")}
          >
            🏛 Central Ministry
          </button>
          <button
            className={`role-tab ${role === "ngo" ? "active" : ""}`}
            onClick={() => handleRoleSwitch("ngo")}
          >
            🏢 NGO Incharge
          </button>
          <button
            className={`role-tab ${role === "inspector" ? "active" : ""}`}
            onClick={() => handleRoleSwitch("inspector")}
          >
            📱 Field Inspector
          </button>
        </div>

        <div className="header-right">
          <span className="live">
            <span className="pulse-dot"></span> 24/7 SURVEILLANCE
          </span>
          <div className="user-badge">
            <span>{user?.full_name || user?.email}</span>
            <small>({user?.role?.toUpperCase()})</small>
          </div>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="layout">
        <aside>
          {/* =================================================================
             1. Central Ministry Navigation
             ================================================================= */}
          {role === "ministry" && (
            <>
              <div className="label">CENTRAL COMMAND</div>
              <NavLink to="/dashboard/central" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🏛 Central Command
              </NavLink>
              <NavLink to="/institutions" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🏢 DoSJE Schemes & Centers
              </NavLink>
              <NavLink to="/risk-map" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🗺 National Risk GIS Map
              </NavLink>

              <div className="label">SURVEILLANCE & AI</div>
              <NavLink to="/cctv" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📹 Live CCTV Grid
              </NavLink>
              <NavLink to="/video-conferencing" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📞 Surprise VC Audit Desk
              </NavLink>
              <NavLink to="/random-assignment" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🎲 AI Random Duty Allocation
              </NavLink>

              <div className="label">AUDITS & EVIDENCE</div>
              <NavLink to="/inspections" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📋 Field Inspections
              </NavLink>
              <NavLink to="/evidence" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📸 Verified Evidence Vault
              </NavLink>
              <NavLink to="/alerts" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🚨 Anomaly & Ghost Alerts
              </NavLink>
            </>
          )}

          {/* =================================================================
             2. NGO / Institute Incharge Navigation
             ================================================================= */}
          {role === "ngo" && (
            <>
              <div className="label">FACILITY PORTAL</div>
              <NavLink to="/dashboard/ngo" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🏢 Facility Command Desk
              </NavLink>
              <NavLink to="/cctv" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📹 My 4-Camera CCTV Feeds
              </NavLink>

              <div className="label">DAILY OPERATIONS</div>
              <NavLink to="/dashboard/ngo" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📝 Daily Biometric Punch
              </NavLink>
              <NavLink to="/dashboard/ngo" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                👥 Beneficiary Roster
              </NavLink>
              <NavLink to="/inspections" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📜 Past Inspection Audits
              </NavLink>

              <div className="label">GOVERNMENT COMPLIANCE</div>
              <NavLink to="/ngo/compliance" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                🏛 Submit Compliance & ATR to Govt
              </NavLink>
            </>
          )}

          {/* =================================================================
             3. Field Inspector Navigation
             ================================================================= */}
          {role === "inspector" && (
            <>
              <div className="label">FIELD WORKBENCH</div>
              <NavLink to="/inspector-workbench" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📝 On-Site Inspection Workbench
              </NavLink>
              <NavLink to="/inspections" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📋 My Assigned Duties
              </NavLink>
              <NavLink to="/evidence" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
                📸 Verified Evidence Chain
              </NavLink>
            </>
          )}

          <div className="profile">
            <b>{user?.full_name || "Official User"}</b>
            <small>
              {role === "ministry" && "Ministry Administrator"}
              {role === "ngo" && `Project Director • ${user?.institution_id || "DDRS-Salem"}`}
              {role === "inspector" && `Field PMU Officer • ${user?.assigned_district || "Salem"}`}
            </small>
          </div>
        </aside>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
