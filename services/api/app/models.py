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
    role = Column(String, nullable=False)  # ministry, inspector, ngo
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class InstitutionDB(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    attendance = Column(Float, default=0.0)
    beneficiaries = Column(Integer, default=0)
    inspections = Column(Integer, default=0)
    report_variance = Column(Float, default=0.0)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), default=utc_now)

class InspectionDB(Base):
    __tablename__ = "inspections"

    id = Column(String, primary_key=True, index=True)
    institution_id = Column(String, nullable=False, index=True)
    inspector_id = Column(String, nullable=True)
    inspector_name = Column(String, nullable=False)
    status = Column(String, default="assigned")  # assigned, priority, in_progress, completed
    priority = Column(Boolean, default=False)
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
    type = Column(String, nullable=False)  # high_risk, anomaly, evidence_failure, priority_inspection, variance
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
    recommendation = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    analyzed_at = Column(DateTime(timezone=True), default=utc_now)
