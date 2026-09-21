import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from services.api.app.database import engine, Base, SessionLocal
from services.api.app.models import (
    UserDB, InstitutionDB, InstitutionMetricDB, ExternalDataObservationDB, InspectionDB, EvidenceDB, AlertDB, RiskAnalysisDB,
    CCTVFeedDB, VCSessionDB, BeneficiaryDB, BiometricPunchDB, ComplianceNoticeDB, AtrReportDB
)
from services.api.app.auth import hash_password
from services.ai.anomaly import analyze_institution

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

def migrate_schema_if_needed():
    """Ensure existing databases contain all columns used by the current models."""
    if engine.dialect.name != "sqlite":
        with engine.connect() as conn:
            inspector = inspect(engine)

            column_definitions = {
                "users": {
                    "assigned_district": "VARCHAR",
                    "home_district": "VARCHAR",
                    "institution_id": "VARCHAR",
                },
                "institutions": {
                    "scheme": "VARCHAR DEFAULT 'DDRS'",
                    "scheme_category": "VARCHAR DEFAULT 'Rehabilitation'",
                    "sanctioned_capacity": "INTEGER DEFAULT 50",
                    "cctv_enabled": "BOOLEAN DEFAULT TRUE",
                    "biometric_enabled": "BOOLEAN DEFAULT TRUE",
                    "contact_person": "VARCHAR DEFAULT 'Project Director'",
                    "contact_phone": "VARCHAR DEFAULT '+91-9876543210'",
                },
                "inspections": {
                    "is_surprise": "BOOLEAN DEFAULT FALSE",
                    "sealed_until": "TIMESTAMP",
                    "geofence_verified": "BOOLEAN DEFAULT FALSE",
                    "check_in_lat": "DOUBLE PRECISION",
                    "check_in_lng": "DOUBLE PRECISION",
                    "distance_to_target_meters": "DOUBLE PRECISION",
                    "scheme_name": "VARCHAR",
                },
                "risk_analyses": {
                    "ghost_beneficiary_score": "DOUBLE PRECISION DEFAULT 0.0",
                    "factors": "JSON",
                    "peer_deviation_score": "DOUBLE PRECISION DEFAULT 0.0",
                    "model_name": "VARCHAR",
                    "model_version": "VARCHAR",
                    "model_status": "VARCHAR",
                    "reference_population_size": "INTEGER DEFAULT 0",
                    "reference_scope": "VARCHAR",
                },
                "institution_metrics": {
                    "outcome_label": "INTEGER",
                },
                "external_data_observations": {},
            }

            for table_name, definitions in column_definitions.items():
                if table_name not in inspector.get_table_names():
                    continue
                existing = {
                    column["name"]
                    for column in inspector.get_columns(table_name)
                }
                for column_name, sql_type in definitions.items():
                    if column_name not in existing:
                        conn.execute(
                            text(
                                f"ALTER TABLE {table_name} "
                                f"ADD COLUMN {column_name} {sql_type}"
                            )
                        )
            conn.commit()
        return

    with engine.connect() as conn:
        try:
            # Check users columns
            res = conn.execute(text("PRAGMA table_info(users);"))
            cols = [row[1] for row in res.fetchall()]
            if cols:
                if "assigned_district" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN assigned_district VARCHAR;"))
                if "home_district" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN home_district VARCHAR;"))
                if "institution_id" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN institution_id VARCHAR;"))
                conn.commit()

            # Check institutions columns
            res = conn.execute(text("PRAGMA table_info(institutions);"))
            cols = [row[1] for row in res.fetchall()]
            if cols:
                if "scheme" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN scheme VARCHAR DEFAULT 'DDRS';"))
                if "scheme_category" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN scheme_category VARCHAR DEFAULT 'Rehabilitation';"))
                if "sanctioned_capacity" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN sanctioned_capacity INTEGER DEFAULT 50;"))
                if "cctv_enabled" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN cctv_enabled BOOLEAN DEFAULT 1;"))
                if "biometric_enabled" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN biometric_enabled BOOLEAN DEFAULT 1;"))
                if "contact_person" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN contact_person VARCHAR DEFAULT 'Project Director';"))
                if "contact_phone" not in cols:
                    conn.execute(text("ALTER TABLE institutions ADD COLUMN contact_phone VARCHAR DEFAULT '+91-9876543210';"))
                conn.commit()

            # Check inspections columns
            res = conn.execute(text("PRAGMA table_info(inspections);"))
            cols = [row[1] for row in res.fetchall()]
            if cols:
                if "is_surprise" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN is_surprise BOOLEAN DEFAULT 0;"))
                if "sealed_until" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN sealed_until DATETIME;"))
                if "geofence_verified" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN geofence_verified BOOLEAN DEFAULT 0;"))
                if "check_in_lat" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN check_in_lat FLOAT;"))
                if "check_in_lng" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN check_in_lng FLOAT;"))
                if "distance_to_target_meters" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN distance_to_target_meters FLOAT;"))
                if "scheme_name" not in cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN scheme_name VARCHAR;"))
                conn.commit()

            # External data observations are created by Base.metadata.create_all.
            # They do not require ALTER TABLE because this table is introduced as part of Phase 7.

            # Check institution_metrics columns
            res = conn.execute(text("PRAGMA table_info(institution_metrics);"))
            cols = [row[1] for row in res.fetchall()]
            if cols and "outcome_label" not in cols:
                conn.execute(text("ALTER TABLE institution_metrics ADD COLUMN outcome_label INTEGER;"))
                conn.commit()

            # Check risk_analyses columns
            res = conn.execute(text("PRAGMA table_info(risk_analyses);"))
            cols = [row[1] for row in res.fetchall()]
            if cols:
                if "ghost_beneficiary_score" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN ghost_beneficiary_score FLOAT DEFAULT 0.0;"))
                if "factors" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN factors JSON;"))
                if "peer_deviation_score" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN peer_deviation_score FLOAT DEFAULT 0.0;"))
                if "model_name" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN model_name VARCHAR;"))
                if "model_version" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN model_version VARCHAR;"))
                if "model_status" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN model_status VARCHAR;"))
                if "reference_population_size" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN reference_population_size INTEGER DEFAULT 0;"))
                if "reference_scope" not in cols:
                    conn.execute(text("ALTER TABLE risk_analyses ADD COLUMN reference_scope VARCHAR;"))
                conn.commit()
        except Exception:
            pass

def seed_database():
    Base.metadata.create_all(bind=engine)
    migrate_schema_if_needed()
    
    db: Session = SessionLocal()
    try:
        # 1. Seed Users
        if db.query(UserDB).count() == 0:
            users = [
                UserDB(
                    id="USR-01",
                    email="admin@inspect-ai.local",
                    hashed_password=hash_password("Admin@123"),
                    role="ministry",
                    full_name="Dr. Meera Krishnan (Joint Secretary, DoSJE)",
                    assigned_district="National",
                    home_district="Delhi"
                ),
                UserDB(
                    id="USR-02",
                    email="inspector@inspect-ai.local",
                    hashed_password=hash_password("Inspector@123"),
                    role="inspector",
                    full_name="A. Kumar (PMU Senior Auditor)",
                    assigned_district="Salem",
                    home_district="Chennai"
                ),
                UserDB(
                    id="USR-03",
                    email="ngo@inspect-ai.local",
                    hashed_password=hash_password("Ngo@123"),
                    role="ngo",
                    full_name="S. Priya (Project Director, Mother Teresa DDRS)",
                    assigned_district="Salem",
                    home_district="Salem",
                    institution_id="INS-001"
                ),
                UserDB(
                    id="USR-04",
                    email="district@inspect-ai.local",
                    hashed_password=hash_password("District@123"),
                    role="district",
                    full_name="K. Rajesh IAS (District Social Welfare Officer)",
                    assigned_district="Salem",
                    home_district="Madurai"
                )
            ]
            db.add_all(users)
            db.commit()

        # 2. Seed Institutions (DoSJE Schemes)
        if db.query(InstitutionDB).count() == 0:
            institutions = [
                InstitutionDB(
                    id="INS-001",
                    name="Mother Teresa Rehabilitation Centre for Divyangjan",
                    district="Salem",
                    lat=11.6643,
                    lng=78.1460,
                    scheme="DDRS",
                    scheme_category="Deendayal Disabled Rehabilitation Scheme",
                    sanctioned_capacity=60,
                    attendance=41,
                    beneficiaries=58,
                    inspections=5,
                    report_variance=0.04,
                    cctv_enabled=True,
                    biometric_enabled=True,
                    contact_person="S. Priya (Director)",
                    contact_phone="+91-98421-50110",
                    status="active"
                ),
                InstitutionDB(
                    id="INS-002",
                    name="Ananda Nilayam Integrated Senior Citizens Home",
                    district="Erode",
                    lat=11.3410,
                    lng=77.7172,
                    scheme="SENIOR_CITIZENS",
                    scheme_category="Atal Vayo Abhyuday Yojana (AVYAY)",
                    sanctioned_capacity=80,
                    attendance=92,
                    beneficiaries=75,
                    inspections=2,
                    report_variance=0.27,
                    cctv_enabled=True,
                    biometric_enabled=True,
                    contact_person="V. Rangarajan (Superintendent)",
                    contact_phone="+91-94432-88220",
                    status="active"
                ),
                InstitutionDB(
                    id="INS-003",
                    name="SMILE Comprehensive Shelter & Livelihood Center",
                    district="Coimbatore",
                    lat=11.0168,
                    lng=76.9558,
                    scheme="SMILE",
                    scheme_category="Support for Marginalized Individuals",
                    sanctioned_capacity=50,
                    attendance=37,
                    beneficiaries=48,
                    inspections=3,
                    report_variance=0.08,
                    cctv_enabled=True,
                    biometric_enabled=True,
                    contact_person="K. Selvan (Incharge)",
                    contact_phone="+91-98430-12345",
                    status="active"
                ),
                InstitutionDB(
                    id="INS-004",
                    name="Nasha Mukti De-Addiction & Counseling Centre",
                    district="Namakkal",
                    lat=11.2194,
                    lng=78.1670,
                    scheme="NMBA",
                    scheme_category="Nasha Mukt Bharat Abhiyaan",
                    sanctioned_capacity=45,
                    attendance=55,
                    beneficiaries=40,
                    inspections=7,
                    report_variance=0.11,
                    cctv_enabled=True,
                    biometric_enabled=True,
                    contact_person="Dr. Balaji (Chief Medical Counselor)",
                    contact_phone="+91-97890-44550",
                    status="active"
                ),
                InstitutionDB(
                    id="INS-005",
                    name="PM-AJAY Residential Skill & Education Complex",
                    district="Tiruppur",
                    lat=11.1085,
                    lng=77.3411,
                    scheme="PM_AJAY",
                    scheme_category="PM Anusuchit Jaati Abhyuday Yojana",
                    sanctioned_capacity=100,
                    attendance=45,
                    beneficiaries=95,
                    inspections=4,
                    report_variance=0.05,
                    cctv_enabled=True,
                    biometric_enabled=True,
                    contact_person="M. Deepa (Headmaster)",
                    contact_phone="+91-99440-66770",
                    status="active"
                )
            ]
            db.add_all(institutions)
            db.commit()

            # Seed AI Risk Analysis
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
                    ghost_beneficiary_score=analysis.get("ghost_beneficiary_score", 0.0),
                    recommendation=analysis["recommendation"],
                    reason=analysis["reason"],
                    factors=analysis.get("factors", [])
                ))
            db.commit()

        # 3. Seed CCTV Camera Feeds
        if db.query(CCTVFeedDB).count() == 0:
            cctv_entries = []
            institutions = db.query(InstitutionDB).all()
            for inst in institutions:
                cctv_entries.extend([
                    CCTVFeedDB(
                        id=f"CAM-{inst.id}-01",
                        institution_id=inst.id,
                        camera_name="Main Entrance & Gate",
                        stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                        status="ONLINE",
                        ai_crowd_count=8,
                        motion_detected=True
                    ),
                    CCTVFeedDB(
                        id=f"CAM-{inst.id}-02",
                        institution_id=inst.id,
                        camera_name="Kitchen & Dining Hall",
                        stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                        status="ONLINE",
                        ai_crowd_count=24,
                        motion_detected=True
                    ),
                    CCTVFeedDB(
                        id=f"CAM-{inst.id}-03",
                        institution_id=inst.id,
                        camera_name="Dormitories & Living Area",
                        stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
                        status="ONLINE",
                        ai_crowd_count=18,
                        motion_detected=False
                    ),
                    CCTVFeedDB(
                        id=f"CAM-{inst.id}-04",
                        institution_id=inst.id,
                        camera_name="Activity & Vocational Hall",
                        stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                        status="ONLINE" if inst.id != "INS-002" else "OFFLINE",
                        ai_crowd_count=15 if inst.id != "INS-002" else 0,
                        motion_detected=inst.id != "INS-002"
                    )
                ])
            db.add_all(cctv_entries)
            db.commit()

        # 4. Seed Beneficiaries
        if db.query(BeneficiaryDB).count() == 0:
            sample_beneficiaries = [
                BeneficiaryDB(id="BEN-101", institution_id="INS-001", full_name="Karthik M.", category="Locomotor Disability", gender="Male", age=24, aadhaar_masked="XXXX-XXXX-8921", biometric_verified=True, contact_number="+91-98421-11001"),
                BeneficiaryDB(id="BEN-102", institution_id="INS-001", full_name="Revathi S.", category="Hearing Impairment", gender="Female", age=19, aadhaar_masked="XXXX-XXXX-3342", biometric_verified=True, contact_number="+91-98421-11002"),
                BeneficiaryDB(id="BEN-103", institution_id="INS-001", full_name="Sanjay K.", category="Intellectual Disability", gender="Male", age=28, aadhaar_masked="XXXX-XXXX-9910", biometric_verified=True, contact_number="+91-98421-11003"),
                BeneficiaryDB(id="BEN-201", institution_id="INS-002", full_name="Govindasamy N.", category="Senior Citizen (75+)", gender="Male", age=78, aadhaar_masked="XXXX-XXXX-4421", biometric_verified=True, contact_number="+91-94432-22001"),
                BeneficiaryDB(id="BEN-202", institution_id="INS-002", full_name="Kamalambal T.", category="Senior Citizen (Destitute)", gender="Female", age=82, aadhaar_masked="XXXX-XXXX-6612", biometric_verified=True, contact_number="+91-94432-22002"),
                BeneficiaryDB(id="BEN-301", institution_id="INS-003", full_name="Ananya (Rohit)", category="Transgender Beneficiary", gender="Transgender", age=31, aadhaar_masked="XXXX-XXXX-7721", biometric_verified=True, contact_number="+91-98430-33001"),
                BeneficiaryDB(id="BEN-401", institution_id="INS-004", full_name="Mani V.", category="Substance Rehabilitation", gender="Male", age=36, aadhaar_masked="XXXX-XXXX-1152", biometric_verified=True, contact_number="+91-97890-55001"),
                BeneficiaryDB(id="BEN-501", institution_id="INS-005", full_name="Prakash R.", category="PM-AJAY Scholar", gender="Male", age=16, aadhaar_masked="XXXX-XXXX-5521", biometric_verified=True, contact_number="+91-99440-77001")
            ]
            db.add_all(sample_beneficiaries)
            db.commit()

        # 5. Seed Inspections
        if db.query(InspectionDB).count() == 0:
            inspections = [
                InspectionDB(
                    id="INSP-1001",
                    institution_id="INS-002",
                    inspector_id="USR-02",
                    inspector_name="A. Kumar",
                    status="priority",
                    priority=True,
                    is_surprise=True,
                    scheme_name="SENIOR_CITIZENS",
                    geofence_verified=False,
                    scheduled_at=datetime(2026, 9, 21, 14, 0, tzinfo=timezone.utc),
                    notes="AI Surprise Flag: 27% report variance & CCTV offline. Conduct unannounced on-site audit."
                ),
                InspectionDB(
                    id="INSP-1002",
                    institution_id="INS-003",
                    inspector_id="USR-02",
                    inspector_name="A. Kumar",
                    status="assigned",
                    priority=False,
                    is_surprise=False,
                    scheme_name="SMILE",
                    geofence_verified=False,
                    scheduled_at=datetime(2026, 9, 22, 10, 30, tzinfo=timezone.utc),
                    notes="Routine quarterly compliance inspection."
                ),
                InspectionDB(
                    id="INSP-1003",
                    institution_id="INS-001",
                    inspector_id="USR-02",
                    inspector_name="A. Kumar",
                    status="completed",
                    priority=False,
                    is_surprise=False,
                    scheme_name="DDRS",
                    geofence_verified=True,
                    check_in_lat=11.6643,
                    check_in_lng=78.1460,
                    distance_to_target_meters=14.2,
                    scheduled_at=datetime(2026, 9, 15, 11, 0, tzinfo=timezone.utc),
                    notes="Annual DDRS renewal audit completed. All infrastructure meets norms."
                )
            ]
            db.add_all(inspections)
            db.commit()

        # 6. Seed Alerts
        if db.query(AlertDB).count() == 0:
            alerts = [
                AlertDB(
                    id="ALT-101",
                    institution_id="INS-002",
                    institution_name="Ananda Nilayam Integrated Senior Citizens Home",
                    type="ghost_beneficiary",
                    severity="high",
                    message="Ghost Beneficiary Warning: 75 residents enrolled, but CCTV crowd estimation detects max 24 occupants (variance: 68%).",
                    status="unacknowledged"
                ),
                AlertDB(
                    id="ALT-102",
                    institution_id="INS-002",
                    institution_name="Ananda Nilayam Integrated Senior Citizens Home",
                    type="cctv_down",
                    severity="medium",
                    message="CCTV Camera 4 (Activity & Vocational Hall) has been offline for > 48 hours.",
                    status="unacknowledged"
                ),
                AlertDB(
                    id="ALT-103",
                    institution_id="INS-004",
                    institution_name="Nasha Mukti De-Addiction & Counseling Centre",
                    type="variance",
                    severity="medium",
                    message="Biometric punch count diverges by 11% from state scheme average.",
                    status="unacknowledged"
                )
            ]
            db.add_all(alerts)
            db.commit()

        # 7. Seed Evidence
        if db.query(EvidenceDB).count() == 0:
            sample_file_path = os.path.join(UPLOAD_DIR, "salem_ddrs_audit_proof.jpg")
            if not os.path.exists(sample_file_path):
                with open(sample_file_path, "wb") as f:
                    f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00INSPECT_AI_VERIFIED_PHOTO_GPS_TAMPER_PROOF")

            evidence = [
                EvidenceDB(
                    id="EVD-501",
                    institution_id="INS-001",
                    inspection_id="INSP-1003",
                    officer_id="USR-02",
                    file_name="salem_ddrs_audit_proof.jpg",
                    mime_type="image/jpeg",
                    file_size=os.path.getsize(sample_file_path),
                    storage_path=sample_file_path,
                    sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    latitude=11.6643,
                    longitude=78.1460,
                    verified=True,
                    verification_checks={"gps": True, "timestamp": True, "officer_id": True, "institution_id": True, "sha256_integrity": True}
                )
            ]
            db.add_all(evidence)
            db.commit()

        # 8. Seed Compliance Notices
        if db.query(ComplianceNoticeDB).count() == 0:
            notices = [
                ComplianceNoticeDB(
                    id="NOT-2026-001",
                    institution_id="INS-001",
                    notice_type="SHOW_CAUSE",
                    reference_no="MoSJE/DDRS/2026/SC-881",
                    title="Show-Cause Notice: CCTV Downtime in Kitchen & Dining Hall",
                    description="Automated AI Surveillance audit detected that Camera Feed #2 (Kitchen & Dining Hall) was offline for 36 consecutive hours between 14-Sep and 16-Sep. Submit Action Taken Report explaining outage and restoration proofs.",
                    severity="HIGH",
                    issued_by="Dr. Meera Krishnan, MoSJE Central Monitoring Cell",
                    status="PENDING_RESPONSE"
                ),
                ComplianceNoticeDB(
                    id="NOT-2026-002",
                    institution_id="INS-001",
                    notice_type="ATTENDANCE_SHORTFALL",
                    reference_no="MoSJE/DDRS/2026/ATT-419",
                    title="Clarification on Shift Attendance Divergence",
                    description="Biometric punch recorded 54 enrolled residents present while AI optical crowd estimate from Activity Hall stream was 46. Submit reconciliation certificate signed by Medical Superintendent.",
                    severity="MEDIUM",
                    issued_by="PMU Tamil Nadu Regional Directorate",
                    status="PENDING_RESPONSE"
                ),
                ComplianceNoticeDB(
                    id="NOT-2026-003",
                    institution_id="INS-001",
                    notice_type="GRANT_UTILIZATION",
                    reference_no="MoSJE/GFR12A/Q3-2026",
                    title="Mandatory Submission of Q2 Grant-in-Aid Utilization Statement",
                    description="Upload Form GFR 12-A for Q2 FY2026 along with physical and financial progress parameters to enable sanctioning of Q3 residential aid tranche.",
                    severity="LOW",
                    issued_by="Integrated Finance Division, MoSJE",
                    status="PENDING_RESPONSE"
                )
            ]
            db.add_all(notices)
            db.commit()

        # 9. Seed Initial ATR Report
        if db.query(AtrReportDB).count() == 0:
            atr = AtrReportDB(
                id="ATR-2026-0881",
                institution_id="INS-001",
                notice_id="NOT-2026-001",
                category="CCTV_RESTORATION",
                subject="Action Taken Report: Restoration of Kitchen CCTV & Power Inverter Replacement",
                corrective_actions="The optical line power adapter of Camera #2 suffered a surge due to monsoon lightning on 14-Sep. An emergency technician was dispatched on 16-Sep, new 12V 2A adapter and UPS link installed. Stream restored and verified online.",
                director_name="S. Priya (Project Director, INS-001)",
                supporting_hash="sha256_b41a9980fe21c0e3a67d02",
                file_name="cctv_repair_invoice_and_timestamped_proof.pdf",
                status="UNDER_MINISTRY_REVIEW"
            )
            db.add(atr)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
