from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.core.config import BASE_DIR
from app.db.session import SessionLocal
from app.models import MedicalReport, Patient
from app.rag.chunking import chunk_text
from app.rag.extraction import extract_text_from_file
from app.rag.vector_store import add_chunks, collection
from app.utils.report_pdf import generate_report_pdf


REPORT_SECTIONS = {
    "Blood Test 08-10-2026": (
        ("Complete Blood Count", (
            ("Hemoglobin", "13.5 g/dL", "13.0 - 17.0 g/dL"),
            ("WBC Count", "7.2 x10^9/L", "4.0 - 11.0 x10^9/L"),
            ("RBC Count", "4.8 x10^12/L", "4.5 - 5.9 x10^12/L"),
            ("Platelet Count", "250 x10^9/L", "150 - 410 x10^9/L"),
            ("Hematocrit", "41%", "38 - 50%"),
        )),
        ("Remarks", (
            "All parameters are within normal reference ranges. No signs of anemia, infection, "
            "or clotting abnormality detected. Routine follow-up recommended in 6 months.",
        )),
    ),
    "ECG Report": (
        ("ECG Findings", (
            ("Heart Rate", "72 bpm", "60 - 100 bpm"),
            ("PR Interval", "160 ms", "120 - 200 ms"),
            ("QRS Duration", "94 ms", "80 - 120 ms"),
            ("QT Interval", "392 ms", "350 - 440 ms"),
            ("Rhythm", "Normal Sinus Rhythm", "Expected sinus rhythm"),
        )),
        ("Remarks", (
            "Normal sinus rhythm with no evidence of arrhythmia, ischemia, or conduction "
            "abnormality. Heart rate and intervals within normal limits. No signs of myocardial infarction.",
        )),
    ),
    "Allergy & Medication Review": (
        ("Allergies", ("Penicillin - reaction: rash",)),
        ("Current Medications", (
            "Metformin 500mg, twice daily, for Type 2 Diabetes management",
        )),
        ("History", ("Type 2 Diabetes, diagnosed 2023",)),
    ),
    "Follow-up Blood Pressure Check": (
        ("Vitals", (("Blood Pressure", "128/82 mmHg", "Below 130/80 mmHg preferred"),)),
        ("Assessment", ("Blood pressure reading recorded for ongoing monitoring.",)),
    ),
    "Complete Blood Count": (
        ("Complete Blood Count", (
            ("Hemoglobin", "14.8 g/dL", "13.0 - 17.0 g/dL"),
            ("White Blood Cell Count", "6.4 x10^9/L", "4.0 - 11.0 x10^9/L"),
            ("Red Blood Cell Count", "5.02 x10^12/L", "4.5 - 5.9 x10^12/L"),
            ("Platelets", "248 x10^9/L", "150 - 410 x10^9/L"),
            ("Hematocrit", "44.1%", "38 - 50%"),
        )),
        ("Interpretation", ("Results are within expected adult reference ranges.",)),
    ),
    "General Checkup & Prescription": (
        ("Allergies", ("Pollen - reaction: sneezing and itchy eyes",)),
        ("Current Medications", ("Loratadine 10mg, once daily, for allergy management",)),
        ("Conditions", ("Mild hypertension, monitored",)),
        ("Vitals", (
            ("Blood Pressure", "135/88 mmHg", "Below 130/80 mmHg preferred"),
            ("Heart Rate", "76 bpm", "60 - 100 bpm"),
        )),
    ),
    "Routine ECG": (
        ("Routine Electrocardiogram", (
            ("Heart Rate", "72 bpm", "60 - 100 bpm"),
            ("PR Interval", "160 ms", "120 - 200 ms"),
            ("QRS Duration", "88 ms", "80 - 120 ms"),
            ("QT Interval", "390 ms", "350 - 440 ms"),
        )),
        ("Interpretation", ("Sinus rhythm; intervals are within expected limits.",)),
    ),
    "Post-visit Prescription": (
        ("Allergies", ("Shellfish - reaction: swelling",)),
        ("Current Medications", ("Atorvastatin 20mg, once daily, for cholesterol management",)),
        ("Conditions", ("Elevated cholesterol, diagnosed 2025",)),
        ("History", ("Appendectomy, 2019",)),
    ),
}


def regenerate_all_reports() -> None:
    summaries: list[tuple[str, str, str, str]] = []

    with SessionLocal() as db:
        reports = db.scalars(
            select(MedicalReport).join(Patient).order_by(MedicalReport.id)
        ).all()

        for report in reports:
            patient = report.patient
            sections = REPORT_SECTIONS.get(report.title)
            if sections is None:
                summaries.append((str(report.id), patient.full_name, report.title, "no"))
                continue

            report_date = report.created_at
            if report_date.tzinfo is None:
                report_date = report_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
            file_path = Path(report.file_path)
            if not file_path.is_absolute():
                file_path = BASE_DIR / file_path

            generate_report_pdf(
                file_path,
                report.hospital.name,
                patient.full_name,
                patient.patient_code,
                report.title,
                report_date,
                sections,
            )

            collection.delete(where={"report_id": report.id})
            extracted_text = extract_text_from_file(str(file_path))
            if not extracted_text.strip():
                raise RuntimeError(f"Extraction returned no text for {file_path}.")
            add_chunks(
                patient.patient_code,
                report.id,
                report.title,
                chunk_text(extracted_text),
                report_date,
            )
            summaries.append((str(report.id), patient.full_name, report.title, "yes"))

        db.commit()

    print("REPORT ID | PATIENT NAME | TITLE | REGENERATED")
    print("----------+--------------+-------+------------")
    for report_id, patient_name, title, regenerated in summaries:
        print(f"{report_id} | {patient_name} | {title} | {regenerated}")


if __name__ == "__main__":
    regenerate_all_reports()
