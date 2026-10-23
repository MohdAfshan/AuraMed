import hashlib

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Hospital, MedicalReport, Patient, ReportType

TEST_HOSPITAL_KEYS = {
    "AuraMed General Hospital": settings.SEED_HOSPITAL_AURAMED_GENERAL_KEY,
    "Sunrise Diagnostics": settings.SEED_HOSPITAL_SUNRISE_DIAGNOSTICS_KEY,
}


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def seed_database() -> None:
    required_seed_values = {
        "SEED_PATIENT_10234_PHONE": settings.SEED_PATIENT_10234_PHONE,
        "SEED_PATIENT_10235_PHONE": settings.SEED_PATIENT_10235_PHONE,
        "SEED_PATIENT_10236_PHONE": settings.SEED_PATIENT_10236_PHONE,
        "SEED_HOSPITAL_AURAMED_GENERAL_KEY": settings.SEED_HOSPITAL_AURAMED_GENERAL_KEY,
        "SEED_HOSPITAL_SUNRISE_DIAGNOSTICS_KEY": settings.SEED_HOSPITAL_SUNRISE_DIAGNOSTICS_KEY,
    }
    missing_values = [name for name, value in required_seed_values.items() if not value]
    if missing_values:
        raise RuntimeError(
            "Missing required seed configuration: " + ", ".join(missing_values)
        )

    with SessionLocal() as db:
        patients_by_code = {}
        patient_fixtures = [
            ("AURAMED-P-10234", "Aisha Rahman", settings.SEED_PATIENT_10234_PHONE),
            ("AURAMED-P-10235", "Daniel Okafor", settings.SEED_PATIENT_10235_PHONE),
            ("AURAMED-P-10236", "Maya Chen", settings.SEED_PATIENT_10236_PHONE),
        ]
        for patient_code, full_name, phone_number in patient_fixtures:
            patient = db.scalar(
                select(Patient).where(Patient.patient_code == patient_code)
            )
            if patient is None:
                patient = Patient(
                    patient_code=patient_code,
                    full_name=full_name,
                    phone_number=phone_number,
                )
                db.add(patient)
            patients_by_code[patient_code] = patient

        hospitals_by_name = {}
        for name, plaintext_key in TEST_HOSPITAL_KEYS.items():
            hospital = db.scalar(select(Hospital).where(Hospital.name == name))
            if hospital is None:
                hospital = Hospital(name=name, hashed_key=hash_key(plaintext_key))
                db.add(hospital)
            hospitals_by_name[name] = hospital

        db.flush()

        report_fixtures = [
            (
                "AURAMED-P-10234",
                "AuraMed General Hospital",
                ReportType.BLOOD,
                "Complete blood count",
                "reports/auramed-p-10234/cbc.pdf",
            ),
            (
                "AURAMED-P-10234",
                "AuraMed General Hospital",
                ReportType.ECG,
                "Routine ECG",
                "reports/auramed-p-10234/ecg.pdf",
            ),
            (
                "AURAMED-P-10235",
                "Sunrise Diagnostics",
                ReportType.MRI,
                "Brain MRI",
                "reports/auramed-p-10235/brain-mri.pdf",
            ),
            (
                "AURAMED-P-10236",
                "AuraMed General Hospital",
                ReportType.PRESCRIPTION,
                "Post-visit prescription",
                "reports/auramed-p-10236/prescription.pdf",
            ),
        ]
        for patient_code, hospital_name, report_type, title, file_path in report_fixtures:
            existing_report = db.scalar(
                select(MedicalReport).where(MedicalReport.title == title)
            )
            if existing_report is None:
                db.add(
                    MedicalReport(
                        patient=patients_by_code[patient_code],
                        hospital=hospitals_by_name[hospital_name],
                        report_type=report_type,
                        title=title,
                        file_path=file_path,
                    )
                )

        db.commit()
        print("Seed data inserted.")


if __name__ == "__main__":
    seed_database()
