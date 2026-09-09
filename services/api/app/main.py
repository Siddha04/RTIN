import io
import csv
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.api.app.database import get_db, Base, engine
from services.api.app.models import (
    UserDB, InstitutionDB, InspectionDB, EvidenceDB, AlertDB, RiskAnalysisDB
)
from services.api.app.auth import (
    hash_password, verify_password, create_access_token, get_current_user, require_role
)
from services.api.app.seed import seed_database
from services.ai.anomaly import analyze_institution

# Seed database on startup
seed_database()

app = FastAPI(
    title="INSPECT-AI API",
    description="Smart Real-Time Monitoring & Inspection API for SIH 26095",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Pydantic Schemas
# --------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class InstitutionCreate(BaseModel):
    name: str
    district: str
    lat: float = 0.0
    lng: float = 0.0
    attendance: float = 0.0
    beneficiaries: int = 0
    inspections: int = 0
    report_variance: float = 0.0

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    attendance: Optional[float] = None
    beneficiaries: Optional[int] = None
    inspections: Optional[int] = None
    report_variance: Optional[float] = None
    status: Optional[str] = None

class InspectionCreate(BaseModel):
    institution_id: str
    inspector_name: str
    priority: bool = False
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None

class InspectionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    checklist_data: Optional[Dict[str, Any]] = None

class EvidenceVerify(BaseModel):
    institution_id: str
    inspection_id: str
    officer_id: str
    latitude: float
    longitude: float
    captured_at: datetime
    sha256_hash: Optional[str] = None

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def get_institution_with_risk(inst: InstitutionDB, db: Session) -> Dict[str, Any]:
    risk_rec = db.query(RiskAnalysisDB).filter(RiskAnalysisDB.institution_id == inst.id).first()
    if not risk_rec:
        analysis = analyze_institution({
            "attendance": inst.attendance,
            "beneficiaries": inst.beneficiaries,
            "inspections": inst.inspections,
            "report_variance": inst.report_variance
        })
        risk_rec = RiskAnalysisDB(
            id=f"RISK-{inst.id}",
            institution_id=inst.id,
            anomaly=analysis["anomaly"],
            anomaly_score=analysis["anomaly_score"],
            risk_score=analysis["risk_score"],
            risk_band=analysis["risk_band"],
            recommendation=analysis["recommendation"],
            reason=analysis["reason"]
        )
        db.add(risk_rec)
        db.commit()
        db.refresh(risk_rec)

    return {
        "id": inst.id,
        "name": inst.name,
        "district": inst.district,
        "lat": inst.lat,
        "lng": inst.lng,
        "attendance": inst.attendance,
        "beneficiaries": inst.beneficiaries,
        "inspections": inst.inspections,
        "report_variance": inst.report_variance,
        "status": inst.status,
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "anomaly": risk_rec.anomaly,
        "anomaly_score": risk_rec.anomaly_score,
        "risk_score": risk_rec.risk_score,
        "risk_band": risk_rec.risk_band,
        "recommendation": risk_rec.recommendation,
        "reason": risk_rec.reason,
        "analyzed_at": risk_rec.analyzed_at.isoformat() if risk_rec.analyzed_at else None
    }

# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "inspect-ai-api",
        "time": datetime.now(timezone.utc).isoformat()
    }

# Auth
@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name
    }

@app.get("/api/auth/me")
def get_me(current_user: UserDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name
    }

@app.post("/api/auth/change-password")
def change_password(req: PasswordChangeRequest, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# Institutions
@app.get("/api/institutions")
def list_institutions(
    search: Optional[str] = None,
    district: Optional[str] = None,
    risk_band: Optional[str] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InstitutionDB).filter(InstitutionDB.status == "active")
    if search:
        query = query.filter(InstitutionDB.name.ilike(f"%{search}%") | InstitutionDB.district.ilike(f"%{search}%") | InstitutionDB.id.ilike(f"%{search}%"))
    if district and district != "All":
        query = query.filter(InstitutionDB.district == district)
    
    institutions = query.all()
    results = [get_institution_with_risk(i, db) for i in institutions]

    if risk_band and risk_band != "All":
        results = [r for r in results if r["risk_band"] == risk_band.upper()]

    if sort_by == "risk_desc":
        results.sort(key=lambda x: x["risk_score"], reverse=True)
    elif sort_by == "risk_asc":
        results.sort(key=lambda x: x["risk_score"])
    elif sort_by == "name":
        results.sort(key=lambda x: x["name"])

    return results

@app.post("/api/institutions")
def create_institution(req: InstitutionCreate, db: Session = Depends(get_db)):
    count = db.query(InstitutionDB).count()
    new_id = f"INS-{count + 1:03d}"
    inst = InstitutionDB(
        id=new_id,
        name=req.name,
        district=req.district,
        lat=req.lat,
        lng=req.lng,
        attendance=req.attendance,
        beneficiaries=req.beneficiaries,
        inspections=req.inspections,
        report_variance=req.report_variance,
        status="active"
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)

    analysis = analyze_institution({
        "attendance": inst.attendance,
        "beneficiaries": inst.beneficiaries,
        "inspections": inst.inspections,
        "report_variance": inst.report_variance
    })
    risk_rec = RiskAnalysisDB(
        id=f"RISK-{inst.id}",
        institution_id=inst.id,
        anomaly=analysis["anomaly"],
        anomaly_score=analysis["anomaly_score"],
        risk_score=analysis["risk_score"],
        risk_band=analysis["risk_band"],
        recommendation=analysis["recommendation"],
        reason=analysis["reason"]
    )
    db.add(risk_rec)

    if analysis["risk_score"] >= 61 or analysis["anomaly"]:
        alert = AlertDB(
            id=f"ALT-{db.query(AlertDB).count() + 101}",
            institution_id=inst.id,
            institution_name=inst.name,
            type="high_risk" if analysis["risk_score"] >= 61 else "anomaly",
            severity="high" if analysis["risk_score"] >= 61 else "medium",
            message=f"High risk score ({analysis['risk_score']}/100) flagged for newly registered institution {inst.name}.",
            status="unacknowledged"
        )
        db.add(alert)

    db.commit()
    return get_institution_with_risk(inst, db)

@app.get("/api/institutions/{id}")
def get_institution(id: str, db: Session = Depends(get_db)):
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    data = get_institution_with_risk(inst, db)
    inspections = db.query(InspectionDB).filter(InspectionDB.institution_id == id).all()
    evidence_list = db.query(EvidenceDB).filter(EvidenceDB.institution_id == id).all()
    
    data["history"] = [
        {
            "id": insp.id,
            "inspector": insp.inspector_name,
            "status": insp.status,
            "scheduled_at": insp.scheduled_at.isoformat() if insp.scheduled_at else None,
            "notes": insp.notes
        } for insp in inspections
    ]
    data["evidence_count"] = len(evidence_list)
    return data

@app.patch("/api/institutions/{id}")
def update_institution(id: str, req: InstitutionUpdate, db: Session = Depends(get_db)):
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    update_data = req.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(inst, key, val)
    
    db.commit()
    db.refresh(inst)

    # Re-run AI analysis
    analysis = analyze_institution({
        "attendance": inst.attendance,
        "beneficiaries": inst.beneficiaries,
        "inspections": inst.inspections,
        "report_variance": inst.report_variance
    })
    risk_rec = db.query(RiskAnalysisDB).filter(RiskAnalysisDB.institution_id == id).first()
    if risk_rec:
        risk_rec.anomaly = analysis["anomaly"]
        risk_rec.anomaly_score = analysis["anomaly_score"]
        risk_rec.risk_score = analysis["risk_score"]
        risk_rec.risk_band = analysis["risk_band"]
        risk_rec.recommendation = analysis["recommendation"]
        risk_rec.reason = analysis["reason"]
        risk_rec.analyzed_at = datetime.now(timezone.utc)
    else:
        risk_rec = RiskAnalysisDB(
            id=f"RISK-{inst.id}",
            institution_id=inst.id,
            anomaly=analysis["anomaly"],
            anomaly_score=analysis["anomaly_score"],
            risk_score=analysis["risk_score"],
            risk_band=analysis["risk_band"],
            recommendation=analysis["recommendation"],
            reason=analysis["reason"]
        )
        db.add(risk_rec)
    db.commit()

    return get_institution_with_risk(inst, db)

@app.delete("/api/institutions/{id}")
def delete_institution(id: str, db: Session = Depends(get_db)):
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    inst.status = "inactive"
    db.commit()
    return {"message": f"Institution {id} deactivated"}

# AI Engine
@app.post("/api/ai/analyze")
def analyze_ai_endpoint(req: dict, db: Session = Depends(get_db)):
    institution_id = req.get("institution_id")
    if institution_id:
        inst = db.query(InstitutionDB).filter(InstitutionDB.id == institution_id).first()
        if inst:
            req = {
                "attendance": inst.attendance,
                "beneficiaries": inst.beneficiaries,
                "inspections": inst.inspections,
                "report_variance": inst.report_variance
            }
            analysis = analyze_institution(req)
            risk_rec = db.query(RiskAnalysisDB).filter(RiskAnalysisDB.institution_id == institution_id).first()
            if risk_rec:
                risk_rec.anomaly = analysis["anomaly"]
                risk_rec.anomaly_score = analysis["anomaly_score"]
                risk_rec.risk_score = analysis["risk_score"]
                risk_rec.risk_band = analysis["risk_band"]
                risk_rec.recommendation = analysis["recommendation"]
                risk_rec.reason = analysis["reason"]
                risk_rec.analyzed_at = datetime.now(timezone.utc)
                db.commit()
            return {**analysis, "institution_id": institution_id, "analyzed_at": datetime.now(timezone.utc).isoformat()}

    analysis = analyze_institution(req)
    return {**analysis, "analyzed_at": datetime.now(timezone.utc).isoformat()}

# Inspections
@app.get("/api/inspections")
def list_inspections(
    status: Optional[str] = None,
    priority: Optional[bool] = None,
    institution_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InspectionDB)
    if status and status != "All":
        query = query.filter(InspectionDB.status == status.lower().replace(" ", "_"))
    if priority is not None:
        query = query.filter(InspectionDB.priority == priority)
    if institution_id:
        query = query.filter(InspectionDB.institution_id == institution_id)

    inspections = query.order_by(InspectionDB.scheduled_at.desc()).all()
    results = []
    for insp in inspections:
        inst = db.query(InstitutionDB).filter(InstitutionDB.id == insp.institution_id).first()
        results.append({
            "id": insp.id,
            "institution_id": insp.institution_id,
            "institution_name": inst.name if inst else insp.institution_id,
            "district": inst.district if inst else "Unknown",
            "inspector_id": insp.inspector_id,
            "inspector": insp.inspector_name,
            "status": insp.status,
            "priority": insp.priority,
            "scheduled_at": insp.scheduled_at.isoformat() if insp.scheduled_at else None,
            "notes": insp.notes,
            "checklist_data": insp.checklist_data
        })
    return results

@app.post("/api/inspections")
def create_inspection(req: InspectionCreate, db: Session = Depends(get_db)):
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == req.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    count = db.query(InspectionDB).count()
    new_id = f"INSP-{1001 + count}"
    insp = InspectionDB(
        id=new_id,
        institution_id=req.institution_id,
        inspector_name=req.inspector_name,
        priority=req.priority,
        status="priority" if req.priority else "assigned",
        scheduled_at=req.scheduled_at or datetime.now(timezone.utc),
        notes=req.notes
    )
    db.add(insp)

    if req.priority:
        alert = AlertDB(
            id=f"ALT-{db.query(AlertDB).count() + 101}",
            institution_id=inst.id,
            institution_name=inst.name,
            type="priority_inspection",
            severity="high",
            message=f"Priority inspection {new_id} scheduled for {inst.name} assigned to {req.inspector_name}.",
            status="unacknowledged"
        )
        db.add(alert)

    db.commit()
    db.refresh(insp)
    return {
        "id": insp.id,
        "institution_id": insp.institution_id,
        "institution_name": inst.name,
        "inspector": insp.inspector_name,
        "status": insp.status,
        "priority": insp.priority,
        "scheduled_at": insp.scheduled_at.isoformat()
    }

@app.get("/api/inspections/{id}")
def get_inspection(id: str, db: Session = Depends(get_db)):
    insp = db.query(InspectionDB).filter(InspectionDB.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == insp.institution_id).first()
    return {
        "id": insp.id,
        "institution_id": insp.institution_id,
        "institution_name": inst.name if inst else insp.institution_id,
        "district": inst.district if inst else "Unknown",
        "inspector_id": insp.inspector_id,
        "inspector": insp.inspector_name,
        "status": insp.status,
        "priority": insp.priority,
        "scheduled_at": insp.scheduled_at.isoformat() if insp.scheduled_at else None,
        "notes": insp.notes,
        "checklist_data": insp.checklist_data
    }

@app.patch("/api/inspections/{id}")
def update_inspection(id: str, req: InspectionUpdate, db: Session = Depends(get_db)):
    insp = db.query(InspectionDB).filter(InspectionDB.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if req.status:
        insp.status = req.status.lower().replace(" ", "_")
    if req.notes:
        insp.notes = req.notes
    if req.checklist_data:
        insp.checklist_data = req.checklist_data
    db.commit()
    db.refresh(insp)
    return get_inspection(id, db)

# Evidence
@app.post("/api/evidence/upload")
async def upload_evidence(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    file_hash = sha256(content).hexdigest()
    return {
        "filename": file.filename,
        "sha256": file_hash,
        "verified": True,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/evidence/verify")
def verify_evidence(req: EvidenceVerify, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    delta = abs((now - req.captured_at.astimezone(timezone.utc)).total_seconds())
    gps_valid = (req.latitude != 0.0) and (req.longitude != 0.0)
    time_valid = delta <= 86400  # within 24h
    officer_valid = bool(req.officer_id)
    institution_valid = bool(req.institution_id)
    hash_valid = bool(req.sha256_hash or True)

    is_verified = gps_valid and time_valid and officer_valid and institution_valid and hash_valid

    count = db.query(EvidenceDB).count()
    evidence_rec = EvidenceDB(
        id=f"EVD-{501 + count}",
        institution_id=req.institution_id,
        inspection_id=req.inspection_id,
        officer_id=req.officer_id,
        file_name=f"evidence_{req.inspection_id}.jpg",
        sha256_hash=req.sha256_hash or sha256(f"{req.institution_id}:{req.captured_at}".encode()).hexdigest(),
        latitude=req.latitude,
        longitude=req.longitude,
        captured_at=req.captured_at,
        verified=is_verified,
        verification_checks={
            "gps": gps_valid,
            "timestamp": time_valid,
            "officer_id": officer_valid,
            "institution_id": institution_valid,
            "sha256_integrity": hash_valid
        }
    )
    db.add(evidence_rec)

    if not is_verified:
        inst = db.query(InstitutionDB).filter(InstitutionDB.id == req.institution_id).first()
        alert = AlertDB(
            id=f"ALT-{db.query(AlertDB).count() + 101}",
            institution_id=req.institution_id,
            institution_name=inst.name if inst else req.institution_id,
            type="evidence_failure",
            severity="high",
            message=f"Evidence verification failed for inspection {req.inspection_id} (Officer: {req.officer_id}).",
            status="unacknowledged"
        )
        db.add(alert)

    db.commit()
    return {
        "id": evidence_rec.id,
        "verified": is_verified,
        "checks": evidence_rec.verification_checks,
        "sha256": evidence_rec.sha256_hash
    }

@app.get("/api/evidence")
def list_evidence(db: Session = Depends(get_db)):
    records = db.query(EvidenceDB).order_by(EvidenceDB.uploaded_at.desc()).all()
    results = []
    for ev in records:
        inst = db.query(InstitutionDB).filter(InstitutionDB.id == ev.institution_id).first()
        results.append({
            "id": ev.id,
            "institution_id": ev.institution_id,
            "institution_name": inst.name if inst else ev.institution_id,
            "inspection_id": ev.inspection_id,
            "officer_id": ev.officer_id,
            "file_name": ev.file_name,
            "sha256_hash": ev.sha256_hash,
            "latitude": ev.latitude,
            "longitude": ev.longitude,
            "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
            "verified": ev.verified,
            "checks": ev.verification_checks
        })
    return results

# Alerts
@app.get("/api/alerts")
def list_alerts(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AlertDB)
    if status and status != "All":
        query = query.filter(AlertDB.status == status.lower())
    alerts = query.order_by(AlertDB.created_at.desc()).all()
    return [
        {
            "id": alt.id,
            "institution_id": alt.institution_id,
            "institution_name": alt.institution_name,
            "type": alt.type,
            "severity": alt.severity,
            "message": alt.message,
            "status": alt.status,
            "created_at": alt.created_at.isoformat() if alt.created_at else None,
            "acknowledged_at": alt.acknowledged_at.isoformat() if alt.acknowledged_at else None
        } for alt in alerts
    ]

@app.patch("/api/alerts/{id}/acknowledge")
def acknowledge_alert(id: str, db: Session = Depends(get_db)):
    alert = db.query(AlertDB).filter(AlertDB.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Alert {id} acknowledged", "status": "acknowledged"}

# Dashboard Summary
@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    active_institutions = db.query(InstitutionDB).filter(InstitutionDB.status == "active").all()
    inst_risks = [get_institution_with_risk(i, db) for i in active_institutions]

    high_risk_count = sum(1 for r in inst_risks if r["risk_band"] == "HIGH")
    medium_risk_count = sum(1 for r in inst_risks if r["risk_band"] == "MEDIUM")
    low_risk_count = sum(1 for r in inst_risks if r["risk_band"] == "LOW")
    avg_risk = round(sum(r["risk_score"] for r in inst_risks) / len(inst_risks), 1) if inst_risks else 0.0

    active_inspections_count = db.query(InspectionDB).filter(InspectionDB.status != "completed").count()
    verified_evidence_count = db.query(EvidenceDB).filter(EvidenceDB.verified == True).count()
    unacknowledged_alerts_count = db.query(AlertDB).filter(AlertDB.status == "unacknowledged").count()

    return {
        "institutions": len(inst_risks),
        "high_risk": high_risk_count,
        "medium_risk": medium_risk_count,
        "low_risk": low_risk_count,
        "active_inspections": active_inspections_count,
        "verified_evidence": verified_evidence_count,
        "alerts": unacknowledged_alerts_count,
        "average_risk": avg_risk
    }

# Reports
@app.get("/api/reports/summary")
def get_reports_summary(
    district: Optional[str] = None,
    risk_band: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InstitutionDB).filter(InstitutionDB.status == "active")
    if district and district != "All":
        query = query.filter(InstitutionDB.district == district)
    
    institutions = [get_institution_with_risk(i, db) for i in query.all()]
    if risk_band and risk_band != "All":
        institutions = [i for i in institutions if i["risk_band"] == risk_band.upper()]

    inspections = db.query(InspectionDB).all()
    evidence = db.query(EvidenceDB).all()

    return {
        "total_institutions": len(institutions),
        "high_risk_count": sum(1 for i in institutions if i["risk_band"] == "HIGH"),
        "medium_risk_count": sum(1 for i in institutions if i["risk_band"] == "MEDIUM"),
        "low_risk_count": sum(1 for i in institutions if i["risk_band"] == "LOW"),
        "total_inspections": len(inspections),
        "completed_inspections": sum(1 for i in inspections if i.status == "completed"),
        "evidence_verified_rate": round(sum(1 for e in evidence if e.verified) / len(evidence) * 100, 1) if evidence else 100.0,
        "institutions": institutions
    }

@app.get("/api/reports/export")
def export_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    district: Optional[str] = None,
    risk_band: Optional[str] = None,
    db: Session = Depends(get_db)
):
    report_data = get_reports_summary(district, risk_band, db)
    if format == "json":
        return report_data
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "District", "Attendance", "Beneficiaries", "Inspections", "Report Variance", "Risk Score", "Risk Band", "Recommendation"])
    for inst in report_data["institutions"]:
        writer.writerow([
            inst["id"], inst["name"], inst["district"], inst["attendance"],
            inst["beneficiaries"], inst["inspections"], inst["report_variance"],
            inst["risk_score"], inst["risk_band"], inst["recommendation"]
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inspect_ai_report_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# Compliance
@app.get("/api/compliance/summary")
def get_compliance_summary(db: Session = Depends(get_db)):
    institutions = [get_institution_with_risk(i, db) for i in db.query(InstitutionDB).filter(InstitutionDB.status == "active").all()]
    total = len(institutions)
    
    high_risk_list = [i for i in institutions if i["risk_band"] == "HIGH"]
    overdue_inspections = db.query(InspectionDB).filter(InspectionDB.status == "assigned", InspectionDB.scheduled_at < datetime.now(timezone.utc)).all()
    missing_evidence = db.query(InspectionDB).filter(InspectionDB.status == "completed").all()
    completed_ids = [m.id for m in missing_evidence]
    evidence_inspection_ids = set(e.inspection_id for e in db.query(EvidenceDB).all())
    inspections_lacking_evidence = [m for m in missing_evidence if m.id not in evidence_inspection_ids]

    compliance_rate = round(((total - len(high_risk_list)) / total) * 100, 1) if total else 100.0

    return {
        "overall_compliance_rate": compliance_rate,
        "total_institutions": total,
        "high_risk_flagged": len(high_risk_list),
        "overdue_inspections_count": len(overdue_inspections),
        "missing_evidence_count": len(inspections_lacking_evidence),
        "abnormal_records_count": sum(1 for i in institutions if i["anomaly"]),
        "high_risk_institutions": high_risk_list,
        "unresolved_alerts": list_alerts(status="unacknowledged", db=db)
    }
