import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InstitutionsPage } from "./pages/InstitutionsPage";
import { InstitutionDetailPage } from "./pages/InstitutionDetailPage";
import { InspectionsPage } from "./pages/InspectionsPage";
import { RiskMapPage } from "./pages/RiskMapPage";
import { EvidencePage } from "./pages/EvidencePage";
import { AlertsPage } from "./pages/AlertsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { CompliancePage } from "./pages/CompliancePage";
import { SettingsPage } from "./pages/SettingsPage";
import "./styles.css";

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <div className="loading-spinner">Validating session credentials...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/institutions" element={<InstitutionsPage />} />
            <Route path="/institutions/:id" element={<InstitutionDetailPage />} />
            <Route path="/inspections" element={<InspectionsPage />} />
            <Route path="/risk-map" element={<RiskMapPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/compliance" element={<CompliancePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
