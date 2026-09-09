from datetime import datetime, timezone
from sqlalchemy.orm import Session
from services.api.app.database import engine, Base, SessionLocal
from services.api.app.models import UserDB, InstitutionDB, InspectionDB, EvidenceDB, AlertDB, RiskAnalysisDB
from services.api.app.auth import hash_password
from services.ai.anomaly import analyze_institution

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(UserDB).count() == 0:
            users = [
                UserDB(id="USR-01", email="admin@inspect-ai.local", hashed_password=hash_password("Admin@123"), role="ministry", full_name="Meera Krishnan"),
                UserDB(id="USR-02", email="inspector@inspect-ai.local", hashed_password=hash_password("Inspector@123"), role="inspector", full_name="A. Kumar"),
                UserDB(id="USR-03", email="ngo@inspect-ai.local", hashed_password=hash_password("Ngo@123"), role="ngo", full_name="S. Priya")
            ]
            db.add_all(users)
            db.commit()

        if db.query(InstitutionDB).count() == 0:
            institutions = [
                InstitutionDB(id="INS-001", name="Government Higher Secondary School - Salem", district="Salem", lat=11.6643, lng=78.1460, attendance=41, beneficiaries=412, inspections=5, report_variance=0.04),
                InstitutionDB(id="INS-002", name="Community Welfare Institute - Erode", district="Erode", lat=11.3410, lng=77.7172, attendance=92, beneficiaries=510, inspections=2, report_variance=0.27),
                InstitutionDB(id="INS-003", name="Rural Skills Centre - Namakkal", district="Namakkal", lat=11.2194, lng=78.1670, attendance=55, beneficiaries=288, inspections=7, report_variance=0.11),
                InstitutionDB(id="INS-004", name="District Learning Hub - Coimbatore", district="Coimbatore", lat=11.0168, lng=76.9558, attendance=37, beneficiaries=620, inspections=3, report_variance=0.08)
            ]
            db.add_all(institutions)
            db.commit()

            # Seed initial AI risk analysis
            for inst in institutions:
                analysis = analyze_institution({
                    "attendance": inst.attendance,
                    "beneficiaries": inst.beneficiaries,
                    "inspections": inst.inspections,
                    "report_variance": inst.report_variance
                })
                db.add(RiskAnalysisDB(
                    id=f"RISK-{inst.id}",
                    institution_id=inst.id,
                    anomaly=analysis["anomaly"],
                    anomaly_score=analysis["anomaly_score"],
                    risk_score=analysis["risk_score"],
                    risk_band=analysis["risk_band"],
                    recommendation=analysis["recommendation"],
                    reason=analysis["reason"]
                ))
            db.commit()

        if db.query(InspectionDB).count() == 0:
            inspections = [
                InspectionDB(id="INSP-1001", institution_id="INS-002", inspector_id="USR-02", inspector_name="A. Kumar", status="priority", priority=True, scheduled_at=datetime(2026, 9, 10, 10, 30, tzinfo=timezone.utc)),
                InspectionDB(id="INSP-1002", institution_id="INS-003", inspector_id="USR-03", inspector_name="S. Priya", status="assigned", priority=False, scheduled_at=datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)),
                InspectionDB(id="INSP-1003", institution_id="INS-001", inspector_id="USR-02", inspector_name="M. Ravi", status="completed", priority=False, scheduled_at=datetime(2026, 9, 9, 14, 0, tzinfo=timezone.utc))
            ]
            db.add_all(inspections)
            db.commit()

        if db.query(AlertDB).count() == 0:
            alerts = [
                AlertDB(id="ALT-101", institution_id="INS-002", institution_name="Community Welfare Institute - Erode", type="high_risk", severity="high", message="High risk score (87/100) flagged by AI anomaly detection engine.", status="unacknowledged"),
                AlertDB(id="ALT-102", institution_id="INS-003", institution_name="Rural Skills Centre - Namakkal", type="anomaly", severity="medium", message="Moderate attendance record deviation detected.", status="unacknowledged")
            ]
            db.add_all(alerts)
            db.commit()

        if db.query(EvidenceDB).count() == 0:
            evidence = [
                EvidenceDB(
                    id="EVD-501",
                    institution_id="INS-001",
                    inspection_id="INSP-1003",
                    officer_id="USR-02",
                    file_name="salem_hss_verification_photo.jpg",
                    sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    latitude=11.6643,
                    longitude=78.1460,
                    verified=True,
                    verification_checks={"gps": True, "timestamp": True, "officer_id": True, "institution_id": True, "sha256_integrity": True}
                )
            ]
            db.add_all(evidence)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
