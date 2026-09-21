import { request } from "./client";

export interface User {
  id: string;
  email: string;
  role: string;
  full_name: string;
  assigned_district?: string;
  institution_id?: string;
}

export interface Institution {
  id: string;
  name: string;
  district: string;
  lat: number;
  lng: number;
  scheme?: string;
  scheme_category?: string;
  sanctioned_capacity?: number;
  attendance: number;
  beneficiaries: number;
  inspections: number;
  report_variance: number;
  cctv_enabled?: boolean;
  biometric_enabled?: boolean;
  contact_person?: string;
  contact_phone?: string;
  status: string;
  created_at?: string;
  anomaly: boolean;
  anomaly_score: number;
  risk_score: number;
  risk_band: "LOW" | "MEDIUM" | "HIGH";
  ghost_beneficiary_score?: number;
  recommendation: string;
  reason: string;
  factors?: Array<{ metric: string; severity: string; detail: string }>;
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
  is_surprise?: boolean;
  sealed_until?: string;
  geofence_verified?: boolean;
  distance_to_target_meters?: number;
  scheme_name?: string;
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
  checks?: Record<string, boolean>;
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

export interface SchemeSummary {
  scheme: string;
  institution_count: number;
  total_beneficiaries: number;
  high_risk_count: number;
  average_attendance: number;
  status: string;
}

export interface CCTVFeed {
  id: string;
  institution_id: string;
  institution_name: string;
  district: string;
  scheme: string;
  camera_name: string;
  stream_url: string;
  status: "ONLINE" | "OFFLINE" | "WARNING";
  ai_crowd_count: number;
  motion_detected: boolean;
  last_ping?: string;
}

export interface VCCandidate {
  target_type: "INCHARGE" | "STAFF" | "BENEFICIARY";
  name: string;
  role: string;
  contact: string;
  aadhaar_masked?: string;
  institution_id: string;
  institution_name: string;
  scheme: string;
}

export interface VCSession {
  id: string;
  caller_id: string;
  caller_name: string;
  institution_id: string;
  institution_name: string;
  target_type: string;
  target_name: string;
  room_code: string;
  status: string;
  duration_sec: number;
  watermark_data?: any;
  notes?: string;
  created_at: string;
}

export interface Beneficiary {
  id: string;
  institution_id: string;
  full_name: string;
  category: string;
  gender: string;
  age: number;
  aadhaar_masked: string;
  biometric_verified: boolean;
  contact_number: string;
  status: string;
}

export interface BiometricPunch {
  id: string;
  institution_id: string;
  date: string;
  shift: string;
  staff_present: number;
  staff_total: number;
  beneficiaries_present: number;
  beneficiaries_total: number;
  cctv_estimated_headcount: number;
  variance_flag: boolean;
  uploaded_at: string;
}

export interface ComplianceNotice {
  id: string;
  institution_id: string;
  notice_type: string;
  reference_no: string;
  title: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  issued_by: string;
  issued_date: string;
  deadline?: string;
  status: string;
}

export interface AtrReport {
  id: string;
  institution_id: string;
  notice_id?: string;
  category: string;
  subject: string;
  corrective_actions: string;
  director_name: string;
  supporting_hash?: string;
  file_name?: string;
  status: string;
  submitted_at: string;
  ministry_remarks?: string;
}

// API methods
export const api = {
  // Auth
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; role: string; email: string; full_name: string; assigned_district?: string; institution_id?: string }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify(data) }
    ),
  getMe: () => request<User>("/api/auth/me"),
  changePassword: (data: { old_password: string; new_password: string }) =>
    request<{ message: string }>("/api/auth/change-password", { method: "POST", body: JSON.stringify(data) }),

  // Dashboard & Schemes
  getDashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  getSchemesSummary: () => request<SchemeSummary[]>("/api/schemes/summary"),

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

  // AI Analysis & Random Assignment
  analyzeAi: (data: { institution_id?: string; attendance?: number; beneficiaries?: number; inspections?: number; report_variance?: number }) =>
    request<any>("/api/ai/analyze", { method: "POST", body: JSON.stringify(data) }),
  allocateAssignments: (data: { target_count?: number; is_surprise?: boolean }) =>
    request<any[]>("/api/assignment/allocate", { method: "POST", body: JSON.stringify(data) }),

  // CCTV Surveillance
  getCctvFeeds: (params?: { institution_id?: string; scheme?: string }) => {
    const q = new URLSearchParams();
    if (params?.institution_id) q.append("institution_id", params.institution_id);
    if (params?.scheme) q.append("scheme", params.scheme);
    return request<CCTVFeed[]>(`/api/cctv/feeds?${q.toString()}`);
  },
  captureCctvSnapshot: (feed_id: string, inspection_id?: string) =>
    request<any>("/api/cctv/snapshot", { method: "POST", body: JSON.stringify({ feed_id, inspection_id }) }),

  // Video Conferencing (VC)
  getVcCandidate: (institution_id: string, target_type: "INCHARGE" | "STAFF" | "BENEFICIARY" = "BENEFICIARY") =>
    request<VCCandidate>(`/api/vc/random-candidate?institution_id=${institution_id}&target_type=${target_type}`),
  initiateVc: (data: { institution_id: string; target_type: string; target_name: string; target_contact?: string }) =>
    request<any>("/api/vc/initiate", { method: "POST", body: JSON.stringify(data) }),
  finishVc: (data: { session_id: string; duration_sec: number; notes: string; discrepancy_flagged?: boolean }) =>
    request<any>("/api/vc/finish", { method: "POST", body: JSON.stringify(data) }),
  getVcSessions: (institution_id?: string) => {
    const q = institution_id ? `?institution_id=${institution_id}` : "";
    return request<VCSession[]>(`/api/vc/sessions${q}`);
  },
  checkIncomingVc: (institution_id: string) =>
    request<{ has_incoming: boolean; session_id?: string; room_code?: string; caller_name?: string; target_name?: string }>(
      `/api/vc/incoming?institution_id=${institution_id}`
    ),

  // Inspections & Geo-fencing
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
  geofenceCheckin: (id: string, coords: { latitude: number; longitude: number }) =>
    request<any>(`/api/inspections/${id}/geofence-checkin`, { method: "POST", body: JSON.stringify(coords) }),
  getInspectionReport: (id: string) => request<any>(`/api/inspections/${id}/report`),

  // Beneficiaries & Biometric (NGO Portal)
  getBeneficiaries: (institution_id?: string) => {
    const q = institution_id ? `?institution_id=${institution_id}` : "";
    return request<Beneficiary[]>(`/api/beneficiaries${q}`);
  },
  submitBiometricPunch: (data: {
    institution_id: string;
    shift: string;
    staff_present: number;
    staff_total: number;
    beneficiaries_present: number;
    beneficiaries_total: number;
    cctv_estimated_headcount?: number;
  }) => request<any>("/api/biometric/punch", { method: "POST", body: JSON.stringify(data) }),
  getBiometricHistory: (institution_id: string) =>
    request<BiometricPunch[]>(`/api/biometric/history?institution_id=${institution_id}`),

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

  // Compliance & ATR Reports
  getComplianceSummary: () => request<any>("/api/compliance/summary"),
  getComplianceNotices: (institution_id?: string) => {
    const q = institution_id ? `?institution_id=${institution_id}` : "";
    return request<ComplianceNotice[]>(`/api/compliance/notices${q}`);
  },
  submitAtrReport: (data: {
    institution_id: string;
    notice_id?: string;
    category: string;
    subject: string;
    corrective_actions: string;
    director_name: string;
    supporting_hash?: string;
    file_name?: string;
  }) => request<any>("/api/compliance/atr", { method: "POST", body: JSON.stringify(data) }),
  getAtrReports: (institution_id?: string) => {
    const q = institution_id ? `?institution_id=${institution_id}` : "";
    return request<AtrReport[]>(`/api/compliance/atr${q}`);
  }
};
