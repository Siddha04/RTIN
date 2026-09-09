import React from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <header>
        <div className="brand">
          <b>INSPECT-AI</b>
          <small>Smart Inspection Command Center (SIH 26095)</small>
        </div>
        <div className="header-right">
          <span className="live">● LIVE MONITORING</span>
          <div className="user-badge">
            <span>{user?.full_name || user?.email}</span>
            <small>({user?.role?.toUpperCase()})</small>
          </div>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="layout">
        <aside>
          <div className="label">COMMAND</div>
          <NavLink to="/dashboard" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Dashboard
          </NavLink>
          <NavLink to="/institutions" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Institutions
          </NavLink>
          <NavLink to="/inspections" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Inspections
          </NavLink>
          <NavLink to="/risk-map" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Risk Map
          </NavLink>

          <div className="label">EVIDENCE & ALERTS</div>
          <NavLink to="/evidence" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Evidence
          </NavLink>
          <NavLink to="/alerts" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Alerts
          </NavLink>

          <div className="label">SYSTEM</div>
          <NavLink to="/reports" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Reports
          </NavLink>
          <NavLink to="/compliance" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Compliance
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav ${isActive ? "active" : ""}`}>
            Settings
          </NavLink>

          <div className="profile">
            <b>{user?.full_name}</b>
            <small>{user?.role?.toUpperCase()} ADMIN</small>
          </div>
        </aside>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
