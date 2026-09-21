from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON
from services.api.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # ministry, inspector, ngo, district
    full_name = Column(String, nullable=False)
    assigned_district = Column(String, nullable=True)
    home_district = Column(String, nullable=True)
    institution_id = Column(String, nullable=True)  # Linked institution for NGO role
    created_at = Column(DateTime(timezone=True), default=utc_now)

class InstitutionDB(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    scheme = Column(String, default="DDRS")  # DDRS, SENIOR_CITIZENS, SMILE, NMBA, PM_AJAY
    scheme_category = Column(String, default="Residential Rehabilitation")
    sanctioned_capacity = Column(Integer, default=50)
    attendance = Column(Float, default=0.0)
    beneficiaries = Column(Integer, default=0)
    inspections = Column(Integer, default=0)
    report_variance = Column(Float, default=0.0)
    cctv_enabled = Column(Boolean, default=True)
    biometric_enabled = Column(Boolean, default=True)
    contact_person = Column(String, default="Project Director")
    contact_phone = Column(String, default="+91-9876543210")
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), default=utc_now)

class InstitutionMetricDB(Base):
    __tablename__ = "institution_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(String, nullable=False, index=True)
    scheme = Column(String, nullable=False, index=True)
    attendance = Column(Float, nullable=False, default=0.0)
    beneficiaries = Column(Integer, nullable=False, default=0)
    inspections = Column(Integer, nullable=False, default=0)
    report_variance = Column(Float, nullable=False, default=0.0)
    sanctioned_capacity = Column(Integer, nullable=False, default=0)
    cctv_headcount = Column(Integer, nullable=True)
    source = Column(String, nullable=False, default="SYSTEM")
    recorded_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class InspectionDB(Base):
    __tablename__ = "inspections"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    inspector_id = Column(String, nullable=True)
    inspector_name = Column(String, nullable=False)
    status = Column(String, default="assigned")  # assigned, priority, in_progress, completed
    priority = Column(Boolean, default=False)
    is_surprise = Column(Boolean, default=False)
    sealed_until = Column(DateTime(timezone=True), nullable=True)  # JIT blind disclosure timestamp
    geofence_verified = Column(Boolean, default=False)
    check_in_lat = Column(Float, nullable=True)
    check_in_lng = Column(Float, nullable=True)
    distance_to_target_meters = Column(Float, nullable=True)
    scheme_name = Column(String, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), default=utc_now)
    notes = Column(Text, nullable=True)
    checklist_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class EvidenceDB(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False)
    inspection_id = Column(String, nullable=False)
    officer_id = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True, default="image/jpeg")
    file_size = Column(Integer, nullable=True, default=0)
    storage_path = Column(String, nullable=True)
    sha256_hash = Column(String, nullable=False)
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    captured_at = Column(DateTime(timezone=True), default=utc_now)
    verified = Column(Boolean, default=True)
    verification_checks = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False)
    institution_name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # high_risk, anomaly, ghost_beneficiary, cctv_down, evidence_failure, priority_inspection, variance
    severity = Column(String, nullable=False)  # low, medium, high
    message = Column(Text, nullable=False)
    status = Column(String, default="unacknowledged")  # unacknowledged, acknowledged
    created_at = Column(DateTime(timezone=True), default=utc_now)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

class RiskAnalysisDB(Base):
    __tablename__ = "risk_analyses"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    risk_score = Column(Integer, default=0)
    risk_band = Column(String, nullable=False)  # LOW, MEDIUM, HIGH
    ghost_beneficiary_score = Column(Float, default=0.0)
    recommendation = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    factors = Column(JSON, nullable=True)
    peer_deviation_score = Column(Float, default=0.0)
    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    model_status = Column(String, nullable=True)
    reference_population_size = Column(Integer, default=0)
    reference_scope = Column(String, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), default=utc_now)

class CCTVFeedDB(Base):
    __tablename__ = "cctv_feeds"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    camera_name = Column(String, nullable=False)  # Main Entrance & Gate, Kitchen & Dining, Dormitories, Activity Hall
    stream_url = Column(String, nullable=False)
    status = Column(String, default="ONLINE")  # ONLINE, OFFLINE, WARNING
    ai_crowd_count = Column(Integer, default=0)
    motion_detected = Column(Boolean, default=True)
    last_ping = Column(DateTime(timezone=True), default=utc_now)

class VCSessionDB(Base):
    __tablename__ = "vc_sessions"

    id = Column(String, primary_key=True, index=True)
    caller_id = Column(String, nullable=False)
    caller_name = Column(String, nullable=False)
    institution_id = Column(String, nullable=False, index=True)
    institution_name = Column(String, nullable=False)
    target_type = Column(String, nullable=False)  # INCHARGE, STAFF, BENEFICIARY
    target_name = Column(String, nullable=False)
    target_contact = Column(String, nullable=True)
    room_code = Column(String, nullable=False)
    status = Column(String, default="CONNECTED")  # CALLING, CONNECTED, COMPLETED, MISSED
    duration_sec = Column(Integer, default=0)
    watermark_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class BeneficiaryDB(Base):
    __tablename__ = "beneficiaries"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # Senior Citizen, PwD, Transgender, Ward
    gender = Column(String, default="Other")
    age = Column(Integer, default=45)
    aadhaar_masked = Column(String, nullable=False)
    biometric_verified = Column(Boolean, default=True)
    contact_number = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    registered_at = Column(DateTime(timezone=True), default=utc_now)

class BiometricPunchDB(Base):
    __tablename__ = "biometric_punches"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    date = Column(String, nullable=False)
    shift = Column(String, default="MORNING")
    staff_present = Column(Integer, default=0)
    staff_total = Column(Integer, default=0)
    beneficiaries_present = Column(Integer, default=0)
    beneficiaries_total = Column(Integer, default=0)
    cctv_estimated_headcount = Column(Integer, default=0)
    variance_flag = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

class ComplianceNoticeDB(Base):
    __tablename__ = "compliance_notices"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    notice_type = Column(String, nullable=False)  # SHOW_CAUSE, AUDIT_DISCREPANCY, ATTENDANCE_SHORTFALL, CCTV_OUTAGE
    reference_no = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    issued_by = Column(String, default="MoSJE Inspection Monitoring Cell")
    issued_date = Column(DateTime(timezone=True), default=utc_now)
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="PENDING_RESPONSE")  # PENDING_RESPONSE, RESOLVED, ESCALATED

class AtrReportDB(Base):
    __tablename__ = "atr_reports"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    notice_id = Column(String, nullable=True)
    category = Column(String, nullable=False)  # ATTENDANCE_VARIANCE, CCTV_RESTORATION, INFRASTRUCTURE_SANITATION, UTILIZATION_PROGRESS
    subject = Column(String, nullable=False)
    corrective_actions = Column(Text, nullable=False)
    director_name = Column(String, nullable=False)
    supporting_hash = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    status = Column(String, default="UNDER_MINISTRY_REVIEW")  # UNDER_MINISTRY_REVIEW, COMPLIANCE_ACCEPTED, CLARIFICATION_REQUIRED
    submitted_at = Column(DateTime(timezone=True), default=utc_now)
    ministry_remarks = Column(Text, nullable=True)

