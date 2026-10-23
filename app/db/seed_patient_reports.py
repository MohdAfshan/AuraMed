from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.core.config import BASE_DIR
from app.db.session import SessionLocal
from app.models import Hospital, MedicalReport, Patient, ReportType
from app.rag.chunking import chunk_text
from app.rag.extraction import extract_text_from_file
from app.rag.vector_store import add_chunks


@dataclass(frozen=True)
class ReportFixture:
    patient_code: str
    hospital_name: str
    report_type: ReportType
    title: str
    date: str
    slug: str
    content: tuple[str, ...]


REPORT_FIXTURES = (
    ReportFixture(
        "AURAMED-P-10234",
        "Sunrise Diagnostics",
        ReportType.OTHER,
        "Allergy & Medication Review",
        "2026-09-20",
        "allergy-medication-review",
        (
            "Patient: Amara Patel",
            "Report date: 2026-09-20",
            "Allergies:",
            "  Penicillin - reaction: rash",
            "Current medications:",
            "  Metformin 500mg, twice daily, for Type 2 Diabetes management",
            "History:",
            "  Type 2 Diabetes, diagnosed 2023",
        ),
    ),
    ReportFixture(
        "AURAMED-P-10234",
        "Sunrise Diagnostics",
        ReportType.OTHER,
        "Follow-up Blood Pressure Check",
        "2026-10-12",
        "follow-up-blood-pressure-check",
        (
            "Patient: Amara Patel",
            "Report date: 2026-10-12",
            "Follow-up visit for blood pressure monitoring.",
            "Vitals:",
            "  Blood Pressure: 128/82 mmHg",
            "Assessment: Blood pressure reading recorded for ongoing monitoring.",
        ),
    ),
    ReportFixture(
        "AURAMED-P-10235",
        "Sunrise Diagnostics",
        ReportType.BLOOD,
        "Complete Blood Count",
        "2026-09-15",
        "complete-blood-count",
        (
            "Patient: Daniel Okafor",
            "Report date: 2026-09-15",
            "Complete Blood Count:",
            "  Hemoglobin: 14.8 g/dL",
            "  White Blood Cell Count: 6.4 x10^9/L",
            "  Red Blood Cell Count: 5.02 x10^12/L",
            "  Platelets: 248 x10^9/L",
            "  Hematocrit: 44.1%",
            "Interpretation: Results are within expected adult reference ranges.",
        ),
    ),
    ReportFixture(
        "AURAMED-P-10235",
        "Sunrise Diagnostics",
        ReportType.OTHER,
        "General Checkup & Prescription",
        "2026-10-05",
        "general-checkup-prescription",
        (
            "Patient: Daniel Okafor",
            "Report date: 2026-10-05",
            "Allergies:",
            "  Pollen - reaction: sneezing and itchy eyes",
            "Current medications:",
            "  Loratadine 10mg, once daily, for allergy management",
            "Conditions:",
            "  Mild hypertension, monitored",
            "Vitals:",
            "  Blood Pressure: 135/88 mmHg",
            "  Heart Rate: 76 bpm",
        ),
    ),
    ReportFixture(
        "AURAMED-P-10236",
        "AuraMed General Hospital",
        ReportType.ECG,
        "Routine ECG",
        "2026-09-10",
        "routine-ecg",
        (
            "Patient: Maya Chen",
            "Report date: 2026-09-10",
            "Routine Electrocardiogram:",
            "  Heart Rate: 72 bpm",
            "  PR Interval: 160 ms",
            "  QRS Duration: 88 ms",
            "  QT Interval: 390 ms",
            "Interpretation: Sinus rhythm; intervals are within expected limits.",
        ),
    ),
    ReportFixture(
        "AURAMED-P-10236",
        "AuraMed General Hospital",
        ReportType.PRESCRIPTION,
        "Post-visit Prescription",
        "2026-10-01",
        "post-visit-prescription",
        (
            "Patient: Maya Chen",
            "Report date: 2026-10-01",
            "Allergies:",
            "  Shellfish - reaction: swelling",
            "Current medications:",
            "  Atorvastatin 20mg, once daily, for cholesterol management",
            "Conditions:",
            "  Elevated cholesterol, diagnosed 2025",
            "History:",
            "  Appendectomy, 2019",
        ),
    ),
)


def write_pdf(path: Path, lines: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    _, page_height = letter
    y = page_height - 72
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 18
    pdf.save()


def seed_patient_reports() -> None:
    with SessionLocal() as db:
        patients = {
            patient.patient_code: patient
            for patient in db.scalars(select(Patient)).all()
        }
        hospitals = {
            hospital.name: hospital
            for hospital in db.scalars(select(Hospital)).all()
        }

        for fixture in REPORT_FIXTURES:
            patient = patients.get(fixture.patient_code)
            hospital = hospitals.get(fixture.hospital_name)
            if patient is None or hospital is None:
                raise SystemExit(
                    f"Missing patient or hospital for report {fixture.title}."
                )

            report_date = datetime.strptime(fixture.date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            file_path = Path("reports") / fixture.patient_code / f"{fixture.slug}.pdf"
            absolute_path = BASE_DIR / file_path
            write_pdf(absolute_path, fixture.content)

            report = db.scalar(
                select(MedicalReport).where(
                    MedicalReport.patient_id == patient.id,
                    MedicalReport.title == fixture.title,
                )
            )
            if report is None:
                report = MedicalReport(
                    patient=patient,
                    hospital=hospital,
                    report_type=fixture.report_type,
                    title=fixture.title,
                    file_path=file_path.as_posix(),
                    created_at=report_date,
                )
                db.add(report)
                db.flush()
            else:
                report.file_path = file_path.as_posix()
                report.created_at = report_date

            extracted_text = extract_text_from_file(str(absolute_path))
            if not extracted_text.strip():
                raise RuntimeError(f"Extraction returned no text for {absolute_path}.")
            add_chunks(
                patient.patient_code,
                report.id,
                report.title,
                chunk_text(extracted_text),
                report_date,
            )

        db.commit()

        print("PATIENT | REPORT COUNT | REPORT TITLES | DATES")
        print("--------+---------------+----------------+----------------")
        for patient in sorted(patients.values(), key=lambda item: item.id):
            reports = db.scalars(
                select(MedicalReport)
                .where(MedicalReport.patient_id == patient.id)
                .order_by(MedicalReport.created_at, MedicalReport.id)
            ).all()
            titles = "; ".join(report.title for report in reports)
            dates = "; ".join(report.created_at.date().isoformat() for report in reports)
            print(f"{patient.full_name} | {len(reports)} | {titles} | {dates}")


if __name__ == "__main__":
    seed_patient_reports()
