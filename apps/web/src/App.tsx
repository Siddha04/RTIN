import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { CentralDashboardPage } from "./pages/CentralDashboardPage";
import { NgoDashboardPage } from "./pages/NgoDashboardPage";
import { NgoCompliancePage } from "./pages/NgoCompliancePage";
import { CCTVPage } from "./pages/CCTVPage";
import { VideoConferencePage } from "./pages/VideoConferencePage";
import { RandomAssignmentPage } from "./pages/RandomAssignmentPage";
import { FieldInspectorWorkbenchPage } from "./pages/FieldInspectorWorkbenchPage";
import { InstitutionsPage } from "./pages/InstitutionsPage";
import { InstitutionDetailPage } from "./pages/InstitutionDetailPage";
import { InspectionsPage } from "./pages/InspectionsPage";
import { RiskMapPage } from "./pages/RiskMapPage";
import { EvidencePage } from "./pages/EvidencePage";
import { AlertsPage } from "./pages/AlertsPage";
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

const RoleBasedRedirect: React.FC = () => {
  const { user } = useAuth();
  if (user?.role === "ngo") return <Navigate to="/dashboard/ngo" replace />;
  if (user?.role === "inspector") return <Navigate to="/inspector-workbench" replace />;
  return <Navigate to="/dashboard/central" replace />;
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
            <Route path="/" element={<RoleBasedRedirect />} />
            <Route path="/dashboard" element={<RoleBasedRedirect />} />
            <Route path="/dashboard/central" element={<CentralDashboardPage />} />
            <Route path="/dashboard/ngo" element={<NgoDashboardPage />} />
            <Route path="/ngo/compliance" element={<NgoCompliancePage />} />
            
            <Route path="/cctv" element={<CCTVPage />} />
            <Route path="/video-conferencing" element={<VideoConferencePage />} />
            <Route path="/random-assignment" element={<RandomAssignmentPage />} />
            <Route path="/inspector-workbench" element={<FieldInspectorWorkbenchPage />} />
            <Route path="/mobile-simulator" element={<Navigate to="/inspector-workbench" replace />} />
            <Route path="/inspector" element={<Navigate to="/inspector-workbench" replace />} />

            <Route path="/institutions" element={<InstitutionsPage />} />
            <Route path="/institutions/:id" element={<InstitutionDetailPage />} />
            <Route path="/inspections" element={<InspectionsPage />} />
            <Route path="/risk-map" element={<RiskMapPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Route>

          <Route path="*" element={<RoleBasedRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
