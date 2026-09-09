import { request } from "./client";

export interface User {
  id: string;
  email: string;
  role: string;
  full_name: string;
}

export interface Institution {
  id: string;
  name: string;
  district: string;
  lat: number;
  lng: number;
  attendance: number;
  beneficiaries: number;
  inspections: number;
  report_variance: number;
  status: string;
  created_at?: string;
  anomaly: boolean;
  anomaly_score: number;
  risk_score: number;
  risk_band: "LOW" | "MEDIUM" | "HIGH";
  recommendation: string;
  reason: string;
  analyzed_at?: string;
  history?: any[];
  evidence_count?: number;
}

export interface Inspection {
  id: string;
  institution_id: string;
  institution_name: string;
  district?: string;
  inspector_id?: string;
  inspector: string;
  status: string;
  priority: boolean;
  scheduled_at?: string;
  notes?: string;
  checklist_data?: any;
}

export interface Evidence {
  id: string;
  institution_id: string;
  institution_name?: string;
  inspection_id: string;
  officer_id: string;
  file_name: string;
  sha256_hash: string;
  latitude: number;
  longitude: number;
  captured_at: string;
  verified: boolean;
  checks: Record<string, boolean>;
}

export interface AlertItem {
  id: string;
  institution_id: string;
  institution_name: string;
  type: string;
  severity: "low" | "medium" | "high";
  message: string;
  status: "unacknowledged" | "acknowledged";
  created_at: string;
  acknowledged_at?: string;
}

export interface DashboardSummary {
  institutions: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  active_inspections: number;
  verified_evidence: number;
  alerts: number;
  average_risk: number;
}

// API methods
export const api = {
  // Auth
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; role: string; email: string; full_name: string }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify(data) }
    ),
  getMe: () => request<User>("/api/auth/me"),
  changePassword: (data: { old_password: string; new_password: string }) =>
    request<{ message: string }>("/api/auth/change-password", { method: "POST", body: JSON.stringify(data) }),

  // Dashboard
  getDashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),

  // Institutions
  getInstitutions: (params?: { search?: string; district?: string; risk_band?: string; sort_by?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.append("search", params.search);
    if (params?.district) q.append("district", params.district);
    if (params?.risk_band) q.append("risk_band", params.risk_band);
    if (params?.sort_by) q.append("sort_by", params.sort_by);
    return request<Institution[]>(`/api/institutions?${q.toString()}`);
  },
  createInstitution: (data: Partial<Institution>) =>
    request<Institution>("/api/institutions", { method: "POST", body: JSON.stringify(data) }),
  getInstitution: (id: string) => request<Institution>(`/api/institutions/${id}`),
  updateInstitution: (id: string, data: Partial<Institution>) =>
    request<Institution>(`/api/institutions/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteInstitution: (id: string) =>
    request<{ message: string }>(`/api/institutions/${id}`, { method: "DELETE" }),

  // AI Analysis
  analyzeAi: (data: { institution_id?: string; attendance?: number; beneficiaries?: number; inspections?: number; report_variance?: number }) =>
    request<any>("/api/ai/analyze", { method: "POST", body: JSON.stringify(data) }),

  // Inspections
  getInspections: (params?: { status?: string; priority?: boolean; institution_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append("status", params.status);
    if (params?.priority !== undefined) q.append("priority", String(params.priority));
    if (params?.institution_id) q.append("institution_id", params.institution_id);
    return request<Inspection[]>(`/api/inspections?${q.toString()}`);
  },
  createInspection: (data: { institution_id: string; inspector_name: string; priority?: boolean; notes?: string }) =>
    request<Inspection>("/api/inspections", { method: "POST", body: JSON.stringify(data) }),
  getInspection: (id: string) => request<Inspection>(`/api/inspections/${id}`),
  updateInspection: (id: string, data: { status?: string; notes?: string; checklist_data?: any }) =>
    request<Inspection>(`/api/inspections/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Evidence
  uploadEvidenceFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ filename: string; sha256: string; verified: boolean; uploaded_at: string }>(
      "/api/evidence/upload",
      { method: "POST", body: formData }
    );
  },
  verifyEvidence: (data: {
    institution_id: string;
    inspection_id: string;
    officer_id: string;
    latitude: number;
    longitude: number;
    captured_at: string;
    sha256_hash?: string;
  }) => request<Evidence>("/api/evidence/verify", { method: "POST", body: JSON.stringify(data) }),
  getEvidence: () => request<Evidence[]>("/api/evidence"),

  // Alerts
  getAlerts: (status?: string) =>
    request<AlertItem[]>(`/api/alerts${status ? `?status=${status}` : ""}`),
  acknowledgeAlert: (id: string) =>
    request<{ message: string; status: string }>(`/api/alerts/${id}/acknowledge`, { method: "PATCH" }),

  // Reports
  getReportsSummary: (params?: { district?: string; risk_band?: string }) => {
    const q = new URLSearchParams();
    if (params?.district) q.append("district", params.district);
    if (params?.risk_band) q.append("risk_band", params.risk_band);
    return request<any>(`/api/reports/summary?${q.toString()}`);
  },
  getExportUrl: (format: "json" | "csv", district?: string, risk_band?: string) => {
    const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const q = new URLSearchParams();
    q.append("format", format);
    if (district) q.append("district", district);
    if (risk_band) q.append("risk_band", risk_band);
    return `${BASE_URL}/api/reports/export?${q.toString()}`;
  },

  // Compliance
  getComplianceSummary: () => request<any>("/api/compliance/summary")
};
